"""
Authentication endpoints.
POST /auth/register  — Create account
POST /auth/login     — Obtain JWT tokens
POST /auth/refresh   — Refresh access token
POST /auth/logout    — Invalidate refresh token
GET  /auth/me        — Current user profile
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user, get_current_user_payload
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    TokenRefreshRequest,
    TokenResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()

_DB_UNAVAILABLE = (
    "Database unavailable. Ensure PostgreSQL is running and credentials in .env match "
    "backend/scripts/setup_postgres.sql."
)


def _translate_db_error(exc: Exception) -> HTTPException:
    root = exc
    while root.__cause__ is not None:
        root = root.__cause__
    if isinstance(root, BaseExceptionGroup):
        for sub in root.exceptions:
            return _translate_db_error(sub)  # type: ignore[arg-type]
    if type(root).__name__ == "InvalidPasswordError":
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "PostgreSQL authentication failed for user in DATABASE_URL. "
                "Run backend/scripts/setup_postgres.sql as the postgres superuser."
            ),
        )
    if isinstance(exc, OperationalError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_DB_UNAVAILABLE,
        )
    raise exc


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        return await service.register(body)
    except Exception as exc:
        raise _translate_db_error(exc) from exc


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    try:
        return await service.login(body)
    except HTTPException:
        raise
    except Exception as exc:
        raise _translate_db_error(exc) from exc


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest | None = None,
    payload: dict = Depends(get_current_user_payload),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    refresh_jti = None
    if body and body.refresh_token:
        from app.core.security import decode_token

        refresh_payload = decode_token(body.refresh_token)
        refresh_jti = refresh_payload.get("jti")

    await service.logout(
        user_id=current_user.id,
        access_jti=payload.get("jti"),
        refresh_jti=refresh_jti,
    )
    return None


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
