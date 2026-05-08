import asyncio
import json
import logging
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
import redis.asyncio as aioredis

from app.models.user import User
from app.redis import get_redis
from app.utils.permissions import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

_HEARTBEAT_INTERVAL = 30  # секунд


async def _event_generator(
    request: Request,
    user: User,
    redis: aioredis.Redis,
    last_event_id: str | None,
) -> AsyncGenerator[str, None]:
    channels = [f"sse:user:{user.id}"]
    if user.department_id:
        channels.append(f"sse:department:{user.department_id}")

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
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    last_event_id = request.headers.get("Last-Event-ID")

    return StreamingResponse(
        _event_generator(request, current_user, redis, last_event_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # отключает буферизацию в Nginx
            "Connection": "keep-alive",
        },
    )
