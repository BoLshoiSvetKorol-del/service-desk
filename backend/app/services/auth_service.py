from datetime import timedelta

from jose import JWTError
import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.user import User, UserRole
from app.utils.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


async def seed_admin(db: AsyncSession) -> None:
    existing = await db.scalar(select(User).where(User.username == settings.ADMIN_USERNAME))
    if existing:
        return
    admin = User(
        username=settings.ADMIN_USERNAME,
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        full_name=settings.ADMIN_FULL_NAME,
        role=UserRole.admin,
        is_active=True,
        is_email_verified=True,
    )
    db.add(admin)
    await db.commit()


class AuthService:
    def __init__(self, db: AsyncSession | None, redis: aioredis.Redis):
        self.db = db
        self.redis = redis

    async def login(self, username: str, password: str) -> tuple[str, str, User] | None:
        from sqlalchemy import or_
        user = await self.db.scalar(
            select(User).where(or_(User.username == username, User.email == username))
        )
        if not user or not verify_password(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        access_token = create_access_token(user.id, user.role.value)
        refresh_token, _ = create_refresh_token(user.id)
        return access_token, refresh_token, user

    async def refresh(self, refresh_token: str) -> tuple[str, User] | None:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return None

        if payload.get("type") != "refresh":
            return None

        jti = payload.get("jti")
        if jti and await self.redis.exists(f"blocklist:{jti}"):
            return None

        try:
            user_id = int(payload["sub"])
        except (KeyError, ValueError):
            return None

        user = await self.db.get(User, user_id)
        if not user or not user.is_active:
            return None

        access_token = create_access_token(user.id, user.role.value)
        return access_token, user

    async def logout(self, refresh_token: str) -> None:
        try:
            payload = decode_token(refresh_token)
        except JWTError:
            return
        jti = payload.get("jti")
        if jti:
            ttl = int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
            await self.redis.setex(f"blocklist:{jti}", ttl, "1")
