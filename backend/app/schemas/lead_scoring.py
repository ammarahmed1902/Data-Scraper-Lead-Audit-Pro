"""Lead scoring API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.lead_scoring import LeadClassification, ScoringJobStatus, ScoringJobType
from app.schemas.common import BaseSchema
from app.schemas.lead_discovery import DiscoveredLeadResponse


class ScoringJobResponse(BaseSchema):
    id: uuid.UUID
    job_type: ScoringJobType
    lead_id: uuid.UUID | None = None
    search_id: uuid.UUID | None = None
    status: ScoringJobStatus
    total_leads: int
    processed_leads: int
    failed_leads: int
    error_message: str | None = None
    celery_task_id: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class LeadScoreResponse(BaseSchema):
    id: uuid.UUID
    lead_id: uuid.UUID
    audit_id: uuid.UUID | None = None
    website_quality_score: float | None = None
    seo_opportunity_score: float | None = None
    technical_opportunity_score: float | None = None
    sales_potential_score: float | None = None
    composite_score: float | None = None
    classification: LeadClassification
    opportunities: list[dict[str, Any]] | None = None
    opportunity_summary: dict[str, Any] | None = None
    ranking: int | None = None
    scored_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class RankedLeadResponse(BaseSchema):
    rank: int | None = None
    score: LeadScoreResponse
    lead: DiscoveredLeadResponse


class ScoringDashboardResponse(BaseSchema):
    total_scored: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    average_composite_score: float | None = None
    top_hot_leads: list[RankedLeadResponse] = Field(default_factory=list)


class ScoringQueuedResponse(BaseSchema):
    job_id: uuid.UUID
    status: ScoringJobStatus
    message: str = "Scoring job queued"


class OpportunityReportResponse(BaseSchema):
    lead_id: uuid.UUID
    business_name: str
    classification: LeadClassification
    composite_score: float | None = None
    opportunities: list[dict[str, Any]]
    opportunity_summary: dict[str, Any] | None = None
