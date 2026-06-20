"""
Centralized application configuration.
All environment variables are loaded and validated here via Pydantic Settings.
"""

from functools import lru_cache

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
    AUTO_GENERATE_REPORTS: bool = True

    # Lead Discovery (Phase 01)
    DISCOVERY_USER_AGENT: str = "LeadAuditPro/1.0 (contact@leadaudit.pro)"
    DISCOVERY_REQUEST_DELAY_SECONDS: float = 1.0
    DISCOVERY_MAX_RESULTS_PER_SEARCH: int = 100
    DISCOVERY_MAX_PAGES_PER_SEARCH: int = 3
    DISCOVERY_PAGE_SIZE: int = 50
    DISCOVERY_ENRICH_WEBSITES: bool = True
    DISCOVERY_PROFILE_SCRAPE_ENABLED: bool = True
    DISCOVERY_MAX_PROFILES_PER_SEARCH: int = 25
    DISCOVERY_HTTP_MAX_RETRIES: int = 3
    DISCOVERY_HTTP_BACKOFF_SECONDS: float = 2.0

    # Business Enrichment (Phase 02)
    ENRICHMENT_REQUEST_DELAY_SECONDS: float = 0.75
    ENRICHMENT_MAX_PAGES: int = 6
    ENRICHMENT_FETCH_TIMEOUT_SECONDS: float = 20.0

    # Dev: use in-memory token store when Redis is unavailable
    USE_MEMORY_TOKEN_STORE: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str) -> str:
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
