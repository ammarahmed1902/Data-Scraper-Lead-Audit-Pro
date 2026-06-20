"""User schemas."""

import uuid
from datetime import datetime

from pydantic import EmailStr, Field

from app.core.security import UserRole
from app.schemas.common import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER
    phone: str | None = None
    timezone: str = "UTC"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=1, max_length=255)
    role: UserRole | None = None
    phone: str | None = None
    timezone: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase, TimestampMixin):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    avatar_url: str | None = None
    last_login_at: datetime | None = None


class UserListResponse(BaseSchema):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
