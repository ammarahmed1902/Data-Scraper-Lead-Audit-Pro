"""
Analytics endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.analytics import AnalyticsOverview, AuditTrendPoint, ScoreDistribution
from app.services.analytics_service import AnalyticsService

router = APIRouter()


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    date_from: str | None = None,
    date_to: str | None = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_overview(_user_id(payload), date_from, date_to)


@router.get("/trends", response_model=list[AuditTrendPoint])
async def get_audit_trends(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_trends(_user_id(payload), period)


@router.get("/scores", response_model=list[ScoreDistribution])
async def get_score_distribution(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_score_distribution(_user_id(payload))


@router.get("/issues")
async def get_top_issues(
    limit: int = Query(10, ge=1, le=50),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AnalyticsService(db)
    return await service.get_top_issues(_user_id(payload), limit)
