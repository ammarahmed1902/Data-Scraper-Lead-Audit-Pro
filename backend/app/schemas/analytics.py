"""Analytics schemas."""

from typing import Any

from pydantic import Field

from app.schemas.common import BaseSchema


class DashboardStats(BaseSchema):
    total_websites: int = 0
    total_audits: int = 0
    pending_audits: int = 0
    completed_audits: int = 0
    average_score: float | None = None
    audits_this_week: int = 0
    audits_this_month: int = 0


class ScoreDistribution(BaseSchema):
    range_label: str
    count: int


class AuditTrendPoint(BaseSchema):
    date: str
    count: int
    average_score: float | None = None


class AnalyticsOverview(BaseSchema):
    stats: DashboardStats
    score_distribution: list[ScoreDistribution] = []
    audit_trends: list[AuditTrendPoint] = []
    top_issues: list[dict[str, Any]] = []


class AnalyticsFilter(BaseSchema):
    date_from: str | None = None
    date_to: str | None = None
    status: str | None = None
    min_score: float | None = Field(None, ge=0, le=100)
    max_score: float | None = Field(None, ge=0, le=100)
