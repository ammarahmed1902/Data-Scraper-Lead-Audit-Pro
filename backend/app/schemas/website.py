"""Website schemas."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_validator

from app.models.website import WebsiteStatus
from app.schemas.common import BaseSchema, TimestampMixin
from app.utils.helpers import is_valid_url, normalize_url


class WebsiteBase(BaseSchema):
    url: str = Field(..., max_length=2048)
    company_name: Optional[str] = Field(None, max_length=255)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    industry: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

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
    websites: List[WebsiteCreate] = Field(..., min_length=1, max_length=500)


class WebsiteBulkResult(BaseSchema):
    created: int
    skipped: int
    errors: List[dict[str, str]] = []


class WebsiteUpdate(BaseSchema):
    url: Optional[str] = Field(None, max_length=2048)
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    industry: Optional[str] = None
    status: Optional[WebsiteStatus] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
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
    last_audited_at: Optional[datetime] = None


class WebsiteListResponse(BaseSchema):
    id: uuid.UUID
    url: str
    domain: str
    company_name: Optional[str] = None
    status: WebsiteStatus
    last_audited_at: Optional[datetime] = None
    created_at: datetime
