"""
Business enrichment endpoints.
POST   /enrichment/leads/{lead_id}       — Enrich single lead
POST   /enrichment/searches/{search_id}  — Bulk enrich search leads
GET    /enrichment/jobs/{job_id}         — Job status
GET    /enrichment/leads/{lead_id}       — Enrichment data for lead
GET    /enrichment/enrichments           — List enrichments (paginated)
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import limiter
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.enrichment import (
    BusinessEnrichmentListResponse,
    BusinessEnrichmentResponse,
    EnrichmentJobResponse,
    EnrichmentQueuedResponse,
)
from app.services.enrichment_service import EnrichmentService

router = APIRouter()
logger = structlog.get_logger(__name__)


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.post(
    "/leads/{lead_id}",
    response_model=EnrichmentQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("10/minute")
async def enrich_lead(
    request: Request,
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    logger.info("enrichment_api_single", user_id=str(user_id), lead_id=str(lead_id))
    service = EnrichmentService(db)
    return await service.enrich_lead(lead_id, user_id)


@router.post(
    "/searches/{search_id}",
    response_model=EnrichmentQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("5/minute")
async def enrich_search(
    request: Request,
    search_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    logger.info("enrichment_api_bulk", user_id=str(user_id), search_id=str(search_id))
    service = EnrichmentService(db)
    return await service.enrich_search(search_id, user_id)


@router.get("/jobs/{job_id}", response_model=EnrichmentJobResponse)
async def get_enrichment_job(
    job_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = EnrichmentService(db)
    return await service.get_job(job_id, _user_id(payload))


@router.get("/leads/{lead_id}", response_model=BusinessEnrichmentResponse)
async def get_lead_enrichment(
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = EnrichmentService(db)
    return await service.get_lead_enrichment(lead_id, _user_id(payload))


@router.get("/enrichments", response_model=PaginatedResponse[BusinessEnrichmentListResponse])
async def list_enrichments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = EnrichmentService(db)
    return await service.list_enrichments(_user_id(payload), page, page_size, status_filter)
