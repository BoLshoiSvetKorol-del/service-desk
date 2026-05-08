from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    APP_NAME: str = "Service Desk"
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str

    DATABASE_URL: str
    REDIS_URL: str = "redis://redis:6379/0"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    SENDGRID_API_KEY: str = ""
    MAIL_FROM: str = "noreply@servicedesk.local"

    STORAGE_BACKEND: str = "local"
    UPLOAD_PATH: str = "/app/uploads"
    MAX_FILE_SIZE_MB: int = 10

    CORS_ORIGINS: list[str] = ["http://localhost", "http://localhost:3000"]

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "changeme"
    ADMIN_EMAIL: str = "admin@servicedesk.local"
    ADMIN_FULL_NAME: str = "Administrator"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// scheme")
        return v

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
