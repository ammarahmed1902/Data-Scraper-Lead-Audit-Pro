"""Lead discovery API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import Field, field_validator

from app.models.lead_discovery import DiscoverySearchStatus
from app.schemas.common import BaseSchema, PaginatedResponse


class DiscoverySearchCreate(BaseSchema):
    industry_keyword: str = Field(..., min_length=2, max_length=255)
    country: str = Field(..., min_length=2, max_length=100)
    state: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    data_source_category: str = Field(..., min_length=2, max_length=100)
    data_source_website: str = Field(..., min_length=2, max_length=100)

    @field_validator("industry_keyword")
    @classmethod
    def validate_industry(cls, v: str) -> str:
        value = v.strip()
        if len(value) < 2:
            raise ValueError("Industry keyword is required and must be at least 2 characters.")
        return value

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        value = v.strip()
        if len(value) < 2:
            raise ValueError("Country is required and must be at least 2 characters.")
        return value

    @field_validator("state", "city")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return v
        stripped = v.strip()
        return stripped or None


class DiscoverySearchResponse(BaseSchema):
    id: uuid.UUID
    industry_keyword: str
    country: str
    state: str | None = None
    city: str | None = None
    data_source_category: str | None = None
    data_source_website: str | None = None
    source_search_url: str | None = None
    status: DiscoverySearchStatus
    total_found: int
    total_new: int
    total_duplicates: int
    pages_processed: int
    error_message: str | None = None
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class DiscoverySearchListResponse(BaseSchema):
    id: uuid.UUID
    industry_keyword: str
    country: str
    state: str | None = None
    city: str | None = None
    data_source_category: str | None = None
    data_source_website: str | None = None
    source_search_url: str | None = None
    status: DiscoverySearchStatus
    total_found: int
    total_new: int
    total_duplicates: int
    created_at: datetime
    completed_at: datetime | None = None


class DiscoveredLeadResponse(BaseSchema):
    id: uuid.UUID
    search_id: uuid.UUID
    business_name: str
    website_url: str | None = None
    domain: str | None = None
    business_category: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    phone_number: str | None = None
    email_address: str | None = None
    social_profiles: dict[str, str] | None = None
    source: str | None = None
    profile_url: str | None = None
    scrape_status: str | None = None
    scrape_errors: list[str] | None = None
    is_duplicate: bool
    imported_website_id: uuid.UUID | None = None
    created_at: datetime


class ImportLeadResponse(BaseSchema):
    lead_id: uuid.UUID
    website_id: uuid.UUID
    message: str


DiscoverySearchPaginatedResponse = PaginatedResponse[DiscoverySearchListResponse]
DiscoveredLeadPaginatedResponse = PaginatedResponse[DiscoveredLeadResponse]
