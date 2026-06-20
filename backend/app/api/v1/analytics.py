"""
Analytics endpoints.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.db_errors import raise_for_database_error
from app.core.security import get_current_user_payload
from app.schemas.analytics import AnalyticsOverview, AuditTrendPoint, ScoreDistribution
from app.services.analytics_service import AnalyticsService

router = APIRouter()
logger = structlog.get_logger(__name__)


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    date_from: str | None = None,
    date_to: str | None = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    try:
        service = AnalyticsService(db)
        return await service.get_overview(user_id, date_from, date_to)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("analytics_overview_failed", user_id=str(user_id))
        raise_for_database_error(exc, context="analytics.overview")


@router.get("/trends", response_model=list[AuditTrendPoint])
async def get_audit_trends(
    period: str = Query("30d", pattern="^(7d|30d|90d|1y)$"),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    try:
        service = AnalyticsService(db)
        return await service.get_trends(user_id, period)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("analytics_trends_failed", user_id=str(user_id), period=period)
        raise_for_database_error(exc, context="analytics.trends")


@router.get("/scores", response_model=list[ScoreDistribution])
async def get_score_distribution(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    try:
        service = AnalyticsService(db)
        return await service.get_score_distribution(user_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("analytics_scores_failed", user_id=str(user_id))
        raise_for_database_error(exc, context="analytics.scores")


@router.get("/issues")
async def get_top_issues(
    limit: int = Query(10, ge=1, le=50),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    try:
        service = AnalyticsService(db)
        return await service.get_top_issues(user_id, limit)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("analytics_issues_failed", user_id=str(user_id), limit=limit)
        raise_for_database_error(exc, context="analytics.issues")
