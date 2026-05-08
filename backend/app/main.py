from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if not settings.TESTING:
        try:
            from app.database import AsyncSessionLocal
            from app.services.auth_service import seed_admin
            from app.services.priority_service import seed_priorities
            async with AsyncSessionLocal() as db:
                await seed_priorities(db)
                await seed_admin(db)
        except Exception as exc:
            print(f"[startup] seed skipped: {exc}")

    yield

    from app.redis import close_redis
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    return {"status": "ok"}
