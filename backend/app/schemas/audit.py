"""Audit schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import Field

from app.models.audit import AuditStatus
from app.schemas.common import BaseSchema

if TYPE_CHECKING:
    from app.models.audit import AuditReport


class AuditCreate(BaseSchema):
    website_id: uuid.UUID


class AuditBulkCreate(BaseSchema):
    website_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)


class AuditLeadCreate(BaseSchema):
    auto_import: bool = True


class SEOReportResponse(BaseSchema):
    id: uuid.UUID
    score: float | None = None
    title_tag: str | None = None
    meta_description: str | None = None
    h1_count: int | None = None
    h2_count: int | None = None
    canonical_url: str | None = None
    internal_links: int | None = None
    external_links: int | None = None
    broken_links: int | None = None
    has_sitemap: bool | None = None
    has_robots_txt: bool | None = None
    mobile_friendly: bool | None = None
    issues: dict[str, Any] | None = None
    recommendations: dict[str, Any] | None = None


class PerformanceReportResponse(BaseSchema):
    id: uuid.UUID
    score: float | None = None
    load_time_ms: float | None = None
    first_contentful_paint: float | None = None
    largest_contentful_paint: float | None = None
    time_to_interactive: float | None = None
    total_blocking_time: float | None = None
    cumulative_layout_shift: float | None = None
    page_size_kb: float | None = None
    request_count: int | None = None
    metrics: dict[str, Any] | None = None
    issues: dict[str, Any] | None = None
    recommendations: dict[str, Any] | None = None


class TechnicalReportResponse(BaseSchema):
    id: uuid.UUID
    score: float | None = None
    ssl_valid: bool | None = None
    ssl_expiry: datetime | None = None
    http_status_code: int | None = None
    server_header: str | None = None
    mobile_friendly: bool | None = None
    indexable: bool | None = None
    accessibility_score: float | None = None
    technologies: dict[str, Any] | None = None
    security_headers: dict[str, Any] | None = None
    dns_records: dict[str, Any] | None = None
    issues: dict[str, Any] | None = None
    recommendations: dict[str, Any] | None = None


class AuditResponse(BaseSchema):
    id: uuid.UUID
    website_id: uuid.UUID
    created_by: uuid.UUID | None = None
    status: AuditStatus
    overall_score: float | None = None
    security_score: float | None = None
    mobile_score: float | None = None
    technical_seo_score: float | None = None
    accessibility_score: float | None = None
    conversion_score: float | None = None
    lead_opportunity_score: float | None = None
    lead_classification: str | None = None
    sales_summary: str | None = None
    category_breakdown: dict[str, Any] | None = None
    summary: str | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    seo_report: SEOReportResponse | None = None
    performance_report: PerformanceReportResponse | None = None
    technical_report: TechnicalReportResponse | None = None


class AuditListResponse(BaseSchema):
    id: uuid.UUID
    website_id: uuid.UUID
    status: AuditStatus
    overall_score: float | None = None
    created_at: datetime
    completed_at: datetime | None = None


def to_audit_response(audit: AuditReport, *, include_reports: bool = False) -> AuditResponse:
    """
    Build AuditResponse from scalar columns only.

    Avoids Pydantic reading lazy-loaded async SQLAlchemy relationships, which
    raises MissingGreenlet during POST /audits response serialization.
    """
    from sqlalchemy.orm import attributes

    data: dict = {
        "id": audit.id,
        "website_id": audit.website_id,
        "created_by": audit.created_by,
        "status": audit.status,
        "overall_score": audit.overall_score,
        "security_score": audit.security_score,
        "mobile_score": audit.mobile_score,
        "technical_seo_score": audit.technical_seo_score,
        "accessibility_score": audit.accessibility_score,
        "conversion_score": audit.conversion_score,
        "lead_opportunity_score": audit.lead_opportunity_score,
        "lead_classification": audit.lead_classification,
        "sales_summary": audit.sales_summary,
        "category_breakdown": audit.category_breakdown,
        "summary": audit.summary,
        "error_message": audit.error_message,
        "started_at": audit.started_at,
        "completed_at": audit.completed_at,
        "created_at": audit.created_at,
        "seo_report": None,
        "performance_report": None,
        "technical_report": None,
    }

    if include_reports:
        state = attributes.instance_state(audit)
        if "seo_report" not in state.unloaded and audit.seo_report is not None:
            data["seo_report"] = SEOReportResponse.model_validate(audit.seo_report)
        if "performance_report" not in state.unloaded and audit.performance_report is not None:
            data["performance_report"] = PerformanceReportResponse.model_validate(
                audit.performance_report
            )
        if "technical_report" not in state.unloaded and audit.technical_report is not None:
            data["technical_report"] = TechnicalReportResponse.model_validate(
                audit.technical_report
            )

    return AuditResponse.model_validate(data)
