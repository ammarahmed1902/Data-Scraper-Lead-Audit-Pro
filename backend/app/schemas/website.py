"""Website schemas."""

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.models.website import WebsiteStatus
from app.schemas.common import BaseSchema, TimestampMixin
from app.utils.helpers import is_valid_url, normalize_url


class WebsiteBase(BaseSchema):
    url: str = Field(..., max_length=2048)
    company_name: str | None = Field(None, max_length=255)
    contact_name: str | None = Field(None, max_length=255)
    contact_email: str | None = Field(None, max_length=255)
    contact_phone: str | None = Field(None, max_length=50)
    industry: str | None = Field(None, max_length=100)
    notes: str | None = None
    tags: list[str] | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        normalized = normalize_url(v)
        if not is_valid_url(normalized):
            raise ValueError("Invalid website URL format")
        return normalized


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteBulkCreate(BaseSchema):
    websites: list[WebsiteCreate] = Field(..., min_length=1, max_length=500)


class WebsiteBulkResult(BaseSchema):
    created: int
    skipped: int
    errors: list[dict[str, str]] = []


class WebsiteUpdate(BaseSchema):
    url: str | None = Field(None, max_length=2048)
    company_name: str | None = None
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    industry: str | None = None
    status: WebsiteStatus | None = None
    notes: str | None = None
    tags: list[str] | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        normalized = normalize_url(v)
        if not is_valid_url(normalized):
            raise ValueError("Invalid website URL format")
        return normalized


class WebsiteResponse(WebsiteBase, TimestampMixin):
    id: uuid.UUID
    owner_id: uuid.UUID
    domain: str
    status: WebsiteStatus
    last_audited_at: datetime | None = None


class WebsiteListResponse(BaseSchema):
    id: uuid.UUID
    url: str
    domain: str
    company_name: str | None = None
    status: WebsiteStatus
    last_audited_at: datetime | None = None
    created_at: datetime
