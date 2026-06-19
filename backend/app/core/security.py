"""
Security utilities: password hashing, JWT creation/validation, RBAC decorators.
"""

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.token_store import get_token_store
from app.models.user import User
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=False)


class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"


ROLE_HIERARCHY: dict[UserRole, int] = {
    UserRole.SUPER_ADMIN: 100,
    UserRole.ADMIN: 80,
    UserRole.MANAGER: 60,
    UserRole.ANALYST: 40,
    UserRole.VIEWER: 20,
}


class TokenPair:
    def __init__(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.access_jti = ""
        self.refresh_jti = ""


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _generate_jti() -> str:
    return str(uuid.uuid4())


def create_token_pair(subject: str, role: UserRole) -> TokenPair:
    access_jti = _generate_jti()
    refresh_jti = _generate_jti()

    access_expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    refresh_expire = datetime.now(timezone.utc) + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    now = datetime.now(timezone.utc)

    access_payload = {
        "sub": subject,
        "role": role.value,
        "type": "access",
        "jti": access_jti,
        "exp": access_expire,
        "iat": now,
    }
    refresh_payload = {
        "sub": subject,
        "type": "refresh",
        "jti": refresh_jti,
        "exp": refresh_expire,
        "iat": now,
    }

    pair = TokenPair(
        access_token=jwt.encode(
            access_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        ),
        refresh_token=jwt.encode(
            refresh_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        ),
    )
    pair.access_jti = access_jti
    pair.refresh_jti = refresh_jti
    return pair


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    jti = payload.get("jti")
    if jti and await get_token_store().is_access_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
        )
    return payload


async def get_current_user(
    payload: dict[str, Any] = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    repo = UserRepository(db)
    user = await repo.get_active_by_id(uuid.UUID(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_role(minimum_role: UserRole):
    async def role_checker(
        payload: dict[str, Any] = Depends(get_current_user_payload),
    ) -> dict[str, Any]:
        user_role = UserRole(payload.get("role", UserRole.VIEWER.value))
        if ROLE_HIERARCHY.get(user_role, 0) < ROLE_HIERARCHY[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return payload

    return role_checker
