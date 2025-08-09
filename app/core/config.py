import os
import secrets
from binascii import hexlify
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Event Management System"
    APP_VERSION: str = "1.0.0"
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "https://localhost:3000"]
    SECRET_KEY: bytes = hexlify(secrets.token_bytes(32))
    JWT_PREFIX: str = "Bearer"
    ALGORITHM: str = "HS256"

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "events_db"
    DB_USER: str = "user"
    DB_PASSWORD: str = "password"
    DB_DRIVER: str = "postgresql+asyncpg"
    DB_DRIVER_SYNC: str = "postgresql"
    DB_URL: Optional[str] = None
    DB_URL_SYNC: Optional[str] = None

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_JSON_FORMAT: bool = True
    LOG_FILE_PATH: str = "/tmp/myapp/logs/app.jsonl"
    LOG_ROTATION: str = "500 MB"
    LOG_RETENTION: str = "7 days"
    LOG_COMPRESSION: str = "zip"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DB_URL = f"{self.DB_DRIVER}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        self.DB_URL_SYNC = f"{self.DB_DRIVER_SYNC}://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


settings = Settings(
    _env_file=os.path.join(os.path.dirname(__file__), "../envs", ".env"),
    _env_file_encoding="utf-8",
)
