import asyncio
import os
import tempfile

os.environ["TESTING"] = "true"
# Always force test DB — never touch production servicedesk database
os.environ["DATABASE_URL"] = "postgresql+asyncpg://servicedesk:servicedesk@postgres:5432/servicedesk_test"
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars!!")
os.environ.setdefault("UPLOAD_PATH", tempfile.mkdtemp(prefix="sd_test_uploads_"))

import pytest
import fakeredis.aioredis
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import Base, get_db
from app.redis import get_redis

TEST_DATABASE_URL = os.environ["DATABASE_URL"]


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    async def _create():
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ticket_number_seq (
                    year INTEGER PRIMARY KEY,
                    last_number INTEGER NOT NULL DEFAULT 0
                )
            """))
        await engine.dispose()

    async def _drop():
        engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()

    _run(_create())
    yield
    _run(_drop())


@pytest.fixture
async def db_session():
    engine = create_async_engine(TEST_DATABASE_URL, poolclass=NullPool)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def fake_redis():
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
async def client(db_session, fake_redis):
    async def override_get_db():
        yield db_session

    async def override_get_redis():
        return fake_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
