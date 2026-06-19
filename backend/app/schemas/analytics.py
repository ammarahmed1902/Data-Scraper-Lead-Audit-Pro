"""Analytics schemas."""

from typing import Any, Dict, List, Optional

from pydantic import Field

from app.schemas.common import BaseSchema


class DashboardStats(BaseSchema):
    total_websites: int = 0
    total_audits: int = 0
    pending_audits: int = 0
    completed_audits: int = 0
    average_score: Optional[float] = None
    audits_this_week: int = 0
    audits_this_month: int = 0


class ScoreDistribution(BaseSchema):
    range_label: str
    count: int


class AuditTrendPoint(BaseSchema):
    date: str
    count: int
    average_score: Optional[float] = None


class AnalyticsOverview(BaseSchema):
    stats: DashboardStats
    score_distribution: List[ScoreDistribution] = []
    audit_trends: List[AuditTrendPoint] = []
    top_issues: List[Dict[str, Any]] = []


class AnalyticsFilter(BaseSchema):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    status: Optional[str] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)
    max_score: Optional[float] = Field(None, ge=0, le=100)
