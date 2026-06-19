"""Pytest configuration and shared fixtures."""

import os

# Set test environment before app imports
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-minimum-32-characters-long")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://leadaudit:leadaudit_secret@localhost:5432/lead_audit_pro",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://leadaudit:leadaudit_secret@localhost:5432/lead_audit_pro",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-minimum-32-chars")
os.environ.setdefault("CSRF_SECRET_KEY", "test-csrf-secret-key-minimum-32-chars")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def anyio_backend():
    return "asyncio"
