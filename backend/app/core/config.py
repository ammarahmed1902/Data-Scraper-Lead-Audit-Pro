"""
Centralized application configuration.
All environment variables are loaded and validated here via Pydantic Settings.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Lead Audit Pro"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = Field(..., min_length=32)
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: PostgresDsn
    DATABASE_URL_SYNC: str

    # Redis
    REDIS_URL: RedisDsn
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    CORS_ORIGINS: str = "http://localhost:3000"
    RATE_LIMIT_PER_MINUTE: int = 60
    CSRF_SECRET_KEY: str = Field(..., min_length=32)

    # Celery
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_WORKER_CONCURRENCY: int = 4

    # Audit & Reports
    PAGESPEED_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    REPORT_STORAGE_PATH: str = "storage/reports"
    EXPORT_STORAGE_PATH: str = "storage/exports"
    REPORT_EXPIRY_DAYS: int = 30
    AUDIT_MAX_RETRIES: int = 3

    # Dev: use in-memory token store when Redis is unavailable
    USE_MEMORY_TOKEN_STORE: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
