"""Authentication schemas."""

from pydantic import EmailStr, Field

from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseSchema):
    refresh_token: str


class LogoutRequest(BaseSchema):
    refresh_token: str | None = None


class AuthResponse(BaseSchema):
    user: UserResponse
    tokens: TokenResponse
