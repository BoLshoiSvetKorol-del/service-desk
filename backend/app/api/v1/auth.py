import secrets
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as aioredis

from app.database import get_db
from app.redis import get_redis
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserResponse, RegisterRequest
from app.services.auth_service import AuthService
from app.utils.permissions import get_current_user
from app.utils.security import hash_password
from app.models.user import User, UserRole

router = APIRouter()

_VERIFY_TTL = 60 * 60 * 24  # 24 hours


@router.post("/login", response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    result = await service.login(data.username, data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    access_token, refresh_token, user = result
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    service = AuthService(db, redis)
    result = await service.refresh(data.refresh_token)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный refresh-токен",
        )
    access_token, user = result
    return TokenResponse(
        access_token=access_token,
        refresh_token=data.refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    data: RefreshRequest,
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    service = AuthService(None, redis)
    await service.logout(data.refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


def _generate_username(email: str, existing: set[str]) -> str:
    """Генерирует уникальный username на основе email."""
    import re
    base = email.split("@")[0]
    base = re.sub(r"[^a-zA-Z0-9_-]", "_", base)[:30]
    candidate = base
    suffix = 2
    while candidate in existing:
        candidate = f"{base[:27]}_{suffix}"
        suffix += 1
    return candidate


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    existing_email = await db.scalar(select(User).where(User.email == data.email))
    if existing_email:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Этот email уже зарегистрирован")

    # Автогенерация username из email
    all_usernames_result = await db.execute(select(User.username))
    all_usernames = {row[0] for row in all_usernames_result.fetchall()}
    username = _generate_username(data.email, all_usernames)

    user = User(
        email=data.email,
        username=username,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role=UserRole.user,
        is_active=True,
        is_email_verified=True,  # AUTO-VERIFIED: email confirmation disabled for local mode
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserResponse.model_validate(user)


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    key = f"email_verify:{token}"
    user_id_raw = await redis.get(key)
    if not user_id_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Токен недействителен или истёк")

    user = await db.get(User, int(user_id_raw))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    user.is_email_verified = True
    await db.commit()
    await db.refresh(user)
    await redis.delete(key)

    return UserResponse.model_validate(user)


@router.post("/resend-verification", status_code=status.HTTP_204_NO_CONTENT)
async def resend_verification(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email уже подтверждён")

    token = secrets.token_urlsafe(32)
    await redis.setex(f"email_verify:{token}", _VERIFY_TTL, str(current_user.id))

    try:
        from app.tasks.email_tasks import send_email_task
        from app.config import settings as _s
        send_email_task.delay(
            to=current_user.email,
            template="email_verification.html",
            context={
                "full_name": current_user.full_name,
                "token": token,
                "verify_url": f"{_s.PORTAL_URL}/portal/verify?token={token}",
            },
            subject="Подтвердите email для входа в Service Desk",
        )
    except Exception:
        pass
