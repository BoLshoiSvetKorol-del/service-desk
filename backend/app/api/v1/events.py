import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import redis.asyncio as aioredis
from jose import JWTError

from app.database import AsyncSessionLocal
from app.models.user import User
from app.redis import get_redis
from app.utils.security import decode_token

router = APIRouter()
logger = logging.getLogger(__name__)

_HEARTBEAT_INTERVAL = 30  # секунд
_bearer_scheme = HTTPBearer()


async def _sse_authenticate(credentials: HTTPAuthorizationCredentials) -> tuple[int, int | None]:
    """Auth for SSE: opens a short-lived DB session, extracts user_id + department_id, then closes it."""
    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")
    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный токен")

    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
        department_id: int | None = user.department_id

    return user_id, department_id


async def _event_generator(
    request: Request,
    user_id: int,
    department_id: int | None,
    redis: aioredis.Redis,
    last_event_id: str | None,
) -> AsyncGenerator[str, None]:
    channels = [f"sse:user:{user_id}"]
    if department_id:
        channels.append(f"sse:department:{department_id}")

    # Отдельный клиент для pub/sub (нельзя использовать основной)
    pubsub_client = redis.client()
    pubsub = pubsub_client.pubsub()
    await pubsub.subscribe(*channels)

    event_id = int(last_event_id) if last_event_id and last_event_id.isdigit() else 0

    try:
        # Сообщаем клиенту что подключились
        yield f": connected to {', '.join(channels)}\n\n"

        while True:
            if await request.is_disconnected():
                break

            try:
                message = await asyncio.wait_for(pubsub.get_message(ignore_subscribe_messages=True), timeout=_HEARTBEAT_INTERVAL)
            except asyncio.TimeoutError:
                message = None

            if message is None:
                # Heartbeat — держим соединение живым
                yield ": ping\n\n"
                continue

            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    event_type = payload.get("event", "message")
                    data = json.dumps(payload.get("data", {}), ensure_ascii=False)
                except Exception:
                    continue

                event_id += 1
                yield f"id: {event_id}\nevent: {event_type}\ndata: {data}\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        try:
            await pubsub.unsubscribe(*channels)
            await pubsub.aclose()
            await pubsub_client.aclose()
        except Exception:
            pass


@router.get("/events")
async def sse_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    redis: aioredis.Redis = Depends(get_redis),
):
    user_id, department_id = await _sse_authenticate(credentials)
    last_event_id = request.headers.get("Last-Event-ID")

    return StreamingResponse(
        _event_generator(request, user_id, department_id, redis, last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # отключает буферизацию в Nginx
            "Connection": "keep-alive",
        },
    )
