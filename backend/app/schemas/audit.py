"""Audit schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from app.models.audit import AuditStatus
from app.schemas.common import BaseSchema


class AuditCreate(BaseSchema):
    website_id: uuid.UUID


class AuditBulkCreate(BaseSchema):
    website_ids: List[uuid.UUID] = Field(..., min_length=1, max_length=100)


class SEOReportResponse(BaseSchema):
    id: uuid.UUID
    score: Optional[float] = None
    title_tag: Optional[str] = None
    meta_description: Optional[str] = None
    h1_count: Optional[int] = None
    internal_links: Optional[int] = None
    external_links: Optional[int] = None
    broken_links: Optional[int] = None
    has_sitemap: Optional[bool] = None
    has_robots_txt: Optional[bool] = None
    mobile_friendly: Optional[bool] = None
    issues: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None


class PerformanceReportResponse(BaseSchema):
    id: uuid.UUID
    score: Optional[float] = None
    load_time_ms: Optional[float] = None
    first_contentful_paint: Optional[float] = None
    largest_contentful_paint: Optional[float] = None
    time_to_interactive: Optional[float] = None
    total_blocking_time: Optional[float] = None
    cumulative_layout_shift: Optional[float] = None
    page_size_kb: Optional[float] = None
    request_count: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None


class TechnicalReportResponse(BaseSchema):
    id: uuid.UUID
    score: Optional[float] = None
    ssl_valid: Optional[bool] = None
    ssl_expiry: Optional[datetime] = None
    http_status_code: Optional[int] = None
    server_header: Optional[str] = None
    technologies: Optional[Dict[str, Any]] = None
    security_headers: Optional[Dict[str, Any]] = None
    dns_records: Optional[Dict[str, Any]] = None
    issues: Optional[Dict[str, Any]] = None
    recommendations: Optional[Dict[str, Any]] = None


class AuditResponse(BaseSchema):
    id: uuid.UUID
    website_id: uuid.UUID
    created_by: Optional[uuid.UUID] = None
    status: AuditStatus
    overall_score: Optional[float] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    seo_report: Optional[SEOReportResponse] = None
    performance_report: Optional[PerformanceReportResponse] = None
    technical_report: Optional[TechnicalReportResponse] = None


class AuditListResponse(BaseSchema):
    id: uuid.UUID
    website_id: uuid.UUID
    status: AuditStatus
    overall_score: Optional[float] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
