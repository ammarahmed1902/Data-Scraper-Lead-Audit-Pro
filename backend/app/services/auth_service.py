"""Authentication business logic."""

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    UserRole,
    create_token_pair,
    decode_token,
    hash_password,
    verify_password,
)
from app.core.token_store import TokenStore, get_token_store
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        token_store: TokenStore | None = None,
    ):
        self.session = session
        self.user_repo = UserRepository(session)
        self.token_store = token_store or get_token_store()

    async def register(self, data: RegisterRequest) -> AuthResponse:
        existing = await self.user_repo.get_by_email(data.email.lower())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name.strip(),
            role=UserRole.VIEWER.value,
            is_active=True,
            is_verified=False,
        )
        user = await self.user_repo.create(user)
        tokens = await self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    async def login(self, data: LoginRequest) -> AuthResponse:
        user = await self.user_repo.get_by_email(data.email.lower())
        if user is None or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated",
            )

        user.last_login_at = datetime.now(timezone.utc)
        await self.user_repo.update(user)

        tokens = await self._issue_tokens(user)
        return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )

        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        stored_user = await self.token_store.get_refresh_token_user(jti)
        if stored_user != user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token revoked or invalid",
            )

        user = await self.user_repo.get_active_by_id(uuid.UUID(user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        await self.token_store.revoke_refresh_token(jti, user_id)
        return await self._issue_tokens(user)

    async def logout(
        self,
        user_id: uuid.UUID,
        access_jti: str | None = None,
        refresh_jti: str | None = None,
    ) -> None:
        if refresh_jti:
            await self.token_store.revoke_refresh_token(refresh_jti, str(user_id))
        else:
            await self.token_store.revoke_all_user_refresh_tokens(str(user_id))

        if access_jti:
            ttl = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
            await self.token_store.blacklist_access_token(access_jti, ttl)

    async def _issue_tokens(self, user: User) -> TokenResponse:
        role = UserRole(user.role)
        pair = create_token_pair(str(user.id), role)
        ttl = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await self.token_store.store_refresh_token(pair.refresh_jti, str(user.id), ttl)
        return TokenResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
        )
