"""User schemas."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, Field

from app.core.security import UserRole
from app.schemas.common import BaseSchema, TimestampMixin


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.VIEWER
    phone: Optional[str] = None
    timezone: str = "UTC"


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserUpdate(BaseSchema):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    role: Optional[UserRole] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampMixin):
    id: uuid.UUID
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None


class UserListResponse(BaseSchema):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
