"""Authentication service unit tests."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.core.security import UserRole, hash_password
from app.core.token_store import InMemoryTokenStore
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService


@pytest.fixture
def token_store():
    return InMemoryTokenStore()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def auth_service(mock_session, token_store):
    return AuthService(mock_session, token_store=token_store)


def _make_user(email: str = "test@example.com", password: str = "password123") -> User:
    return User(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hash_password(password),
        full_name="Test User",
        role=UserRole.VIEWER.value,
        is_active=True,
        is_verified=False,
        timezone="UTC",
        created_at=datetime.now(UTC),
    )


async def _simulate_create(user: User) -> User:
    """Mirror repository create flush/refresh so UserResponse validates."""
    if user.id is None:
        user.id = uuid.uuid4()
    if user.created_at is None:
        user.created_at = datetime.now(UTC)
    if user.timezone is None:
        user.timezone = "UTC"
    return user


@pytest.mark.asyncio
async def test_register_success(auth_service, mock_session):
    auth_service.user_repo = MagicMock()
    auth_service.user_repo.get_by_email = AsyncMock(return_value=None)
    auth_service.user_repo.create = AsyncMock(side_effect=_simulate_create)

    data = RegisterRequest(
        email="new@example.com",
        password="securepass123",
        full_name="New User",
    )
    result = await auth_service.register(data)

    assert result.user.email == "new@example.com"
    assert result.tokens.access_token
    assert result.tokens.refresh_token


@pytest.mark.asyncio
async def test_register_duplicate_email(auth_service):
    auth_service.user_repo = MagicMock()
    auth_service.user_repo.get_by_email = AsyncMock(return_value=_make_user())

    with pytest.raises(HTTPException) as exc:
        await auth_service.register(
            RegisterRequest(
                email="test@example.com",
                password="securepass123",
                full_name="Test",
            )
        )
    assert exc.value.status_code == 409


@pytest.mark.asyncio
async def test_login_success(auth_service):
    user = _make_user()
    auth_service.user_repo = MagicMock()
    auth_service.user_repo.get_by_email = AsyncMock(return_value=user)
    auth_service.user_repo.update = AsyncMock(side_effect=lambda u: u)

    result = await auth_service.login(
        LoginRequest(email="test@example.com", password="password123")
    )
    assert result.user.email == "test@example.com"
    assert result.tokens.access_token


@pytest.mark.asyncio
async def test_login_invalid_credentials(auth_service):
    auth_service.user_repo = MagicMock()
    auth_service.user_repo.get_by_email = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        await auth_service.login(
            LoginRequest(email="wrong@example.com", password="wrong")
        )
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user(auth_service):
    user = _make_user()
    user.is_active = False
    auth_service.user_repo = MagicMock()
    auth_service.user_repo.get_by_email = AsyncMock(return_value=user)

    with pytest.raises(HTTPException) as exc:
        await auth_service.login(
            LoginRequest(email="test@example.com", password="password123")
        )
    assert exc.value.status_code == 403
