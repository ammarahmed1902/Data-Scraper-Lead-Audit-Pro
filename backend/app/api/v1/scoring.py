"""
Lead scoring endpoints.
POST   /scoring/leads/{lead_id}       — Score single lead
POST   /scoring/searches/{search_id}  — Bulk score search
GET    /scoring/jobs/{job_id}         — Job status
GET    /scoring/leads/{lead_id}       — Score for lead
GET    /scoring/leads                 — Ranked leads (filters)
GET    /scoring/dashboard             — Priority dashboard stats
GET    /scoring/leads/{lead_id}/opportunities — Opportunity report
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.lead_scoring import (
    LeadScoreResponse,
    OpportunityReportResponse,
    RankedLeadResponse,
    ScoringDashboardResponse,
    ScoringJobResponse,
    ScoringQueuedResponse,
)
from app.services.lead_scoring_service import LeadScoringService

router = APIRouter()
logger = structlog.get_logger(__name__)


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("/dashboard", response_model=ScoringDashboardResponse)
async def get_scoring_dashboard(
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.get_dashboard(_user_id(payload))


@router.get("/leads", response_model=PaginatedResponse[RankedLeadResponse])
async def list_ranked_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    classification: str | None = Query(None, description="hot, warm, cold"),
    search_id: uuid.UUID | None = None,
    min_composite: float | None = Query(None, ge=0, le=100),
    opportunity: str | None = Query(
        None,
        description="Filter by opportunity category",
    ),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.list_ranked_leads(
        _user_id(payload),
        page,
        page_size,
        classification,
        search_id,
        min_composite,
        opportunity,
    )


@router.post(
    "/leads/{lead_id}",
    response_model=ScoringQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("20/minute")
async def score_lead(
    request: Request,
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.score_lead(lead_id, _user_id(payload))


@router.post(
    "/searches/{search_id}",
    response_model=ScoringQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("5/minute")
async def score_search(
    request: Request,
    search_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.score_search(search_id, _user_id(payload))


@router.get("/jobs/{job_id}", response_model=ScoringJobResponse)
async def get_scoring_job(
    job_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.get_job(job_id, _user_id(payload))


@router.get("/leads/{lead_id}", response_model=LeadScoreResponse)
async def get_lead_score(
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.get_lead_score(lead_id, _user_id(payload))


@router.get("/leads/{lead_id}/opportunities", response_model=OpportunityReportResponse)
async def get_opportunity_report(
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = LeadScoringService(db)
    return await service.get_opportunity_report(lead_id, _user_id(payload))
