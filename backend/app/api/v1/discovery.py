"""
Lead discovery endpoints.
POST   /discovery/searches              — Start a discovery search
GET    /discovery/searches              — Search history (paginated)
GET    /discovery/searches/{id}         — Search status
GET    /discovery/searches/{id}/leads   — Discovered leads (paginated)
POST   /discovery/leads/{id}/import     — Import lead to websites
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.db_errors import raise_for_database_error
from app.core.rate_limit import limiter
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.lead_discovery import (
    DiscoveredLeadResponse,
    DiscoverySearchCreate,
    DiscoverySearchListResponse,
    DiscoverySearchResponse,
    ImportLeadResponse,
)
from app.services.lead_discovery_service import LeadDiscoveryService

router = APIRouter()
logger = structlog.get_logger(__name__)


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.post(
    "/searches",
    response_model=DiscoverySearchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
@limiter.limit("5/minute")
async def create_discovery_search(
    request: Request,
    data: DiscoverySearchCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    logger.info(
        "discovery_api_create",
        user_id=str(user_id),
        source_category=data.data_source_category,
        source_website=data.data_source_website,
        industry=data.industry_keyword,
        country=data.country,
        state=data.state,
        city=data.city,
    )
    try:
        service = LeadDiscoveryService(db)
        search = await service.create_search(data, user_id)
        return DiscoverySearchResponse.model_validate(search)
    except HTTPException:
        raise
    except ValidationError as exc:
        logger.warning("discovery_validation_error", errors=exc.errors())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.errors()[0]["msg"] if exc.errors() else "Invalid request payload.",
        ) from exc
    except Exception as exc:
        logger.exception(
            "discovery_create_failed",
            user_id=str(user_id),
            industry=data.industry_keyword,
            country=data.country,
        )
        raise_for_database_error(exc, context="discovery.create_search")


@router.get("/searches", response_model=PaginatedResponse[DiscoverySearchListResponse])
async def list_discovery_searches(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = LeadDiscoveryService(db)
        return await service.list_searches(_user_id(payload), page, page_size)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("discovery_list_failed", user_id=str(_user_id(payload)))
        raise_for_database_error(exc, context="discovery.list_searches")


@router.get("/searches/{search_id}", response_model=DiscoverySearchResponse)
async def get_discovery_search(
    search_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = LeadDiscoveryService(db)
        return await service.get_search(search_id, _user_id(payload))
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("discovery_get_failed", search_id=str(search_id))
        raise_for_database_error(exc, context="discovery.get_search")


@router.get(
    "/searches/{search_id}/leads",
    response_model=PaginatedResponse[DiscoveredLeadResponse],
)
async def list_discovered_leads(
    search_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_duplicates: bool = Query(False),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = LeadDiscoveryService(db)
        return await service.list_leads(
            search_id,
            _user_id(payload),
            page=page,
            page_size=page_size,
            include_duplicates=include_duplicates,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("discovery_list_leads_failed", search_id=str(search_id))
        raise_for_database_error(exc, context="discovery.list_leads")


@router.post("/leads/{lead_id}/import", response_model=ImportLeadResponse)
async def import_discovered_lead(
    lead_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    try:
        service = LeadDiscoveryService(db)
        lead, website_id = await service.import_lead_to_website(lead_id, _user_id(payload))
        return ImportLeadResponse(
            lead_id=lead.id,
            website_id=website_id,
            message="Lead imported to websites successfully",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("discovery_import_failed", lead_id=str(lead_id))
        raise_for_database_error(exc, context="discovery.import_lead")
