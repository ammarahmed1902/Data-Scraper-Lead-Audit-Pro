"""Business enrichment API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enrichment import EnrichmentJobType, EnrichmentStatus
from app.schemas.common import BaseSchema


class EnrichmentJobResponse(BaseSchema):
    id: uuid.UUID
    job_type: EnrichmentJobType
    lead_id: uuid.UUID | None = None
    search_id: uuid.UUID | None = None
    status: EnrichmentStatus
    total_leads: int
    processed_leads: int
    failed_leads: int
    error_message: str | None = None
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class BusinessEnrichmentResponse(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID
    job_id: uuid.UUID | None = None
    status: EnrichmentStatus
    company_name: str | None = None
    about_us_content: str | None = None
    services: list[str] | None = None
    contact_page_data: dict[str, Any] | None = None
    email_addresses: list[str] | None = None
    phone_numbers: list[str] | None = None
    team_members: list[dict[str, str]] | None = None
    business_description: str | None = None
    technology_stack: list[str] | None = None
    cms_platform: str | None = None
    cms_detected: dict[str, bool] | None = None
    pages_crawled: list[str] | None = None
    error_message: str | None = None
    enriched_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class BusinessEnrichmentListResponse(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID
    status: EnrichmentStatus
    company_name: str | None = None
    cms_platform: str | None = None
    email_addresses: list[str] | None = None
    phone_numbers: list[str] | None = None
    enriched_at: datetime | None = None
    created_at: datetime


class EnrichmentQueuedResponse(BaseSchema):
    job_id: uuid.UUID
    status: EnrichmentStatus
    message: str = Field(default="Enrichment job queued")
