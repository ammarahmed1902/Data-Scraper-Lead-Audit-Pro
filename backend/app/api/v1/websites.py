"""
Website management endpoints.
GET    /websites           — List websites (paginated, filterable)
GET    /websites/{id}      — Get website details
POST   /websites           — Add single website
POST   /websites/bulk      — Bulk import websites
PUT    /websites/{id}      — Update website
DELETE /websites/{id}      — Delete website
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.website import (
    WebsiteBulkCreate,
    WebsiteBulkResult,
    WebsiteCreate,
    WebsiteListResponse,
    WebsiteResponse,
    WebsiteUpdate,
)
from app.services.website_service import WebsiteService

router = APIRouter()


def _owner_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("", response_model=PaginatedResponse[WebsiteListResponse])
async def list_websites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None, max_length=255),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    return await service.list_websites(
        owner_id=_owner_id(payload),
        page=page,
        page_size=page_size,
        status=status_filter,
        search=search,
    )


@router.get("/{website_id}", response_model=WebsiteResponse)
async def get_website(
    website_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    return await service.get_website(website_id, _owner_id(payload))


@router.post("", response_model=WebsiteResponse, status_code=status.HTTP_201_CREATED)
async def create_website(
    data: WebsiteCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    return await service.create_website(data, _owner_id(payload))


@router.post("/bulk", response_model=WebsiteBulkResult, status_code=status.HTTP_202_ACCEPTED)
async def bulk_create_websites(
    data: WebsiteBulkCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    return await service.bulk_create(data, _owner_id(payload))


@router.put("/{website_id}", response_model=WebsiteResponse)
async def update_website(
    website_id: uuid.UUID,
    data: WebsiteUpdate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    return await service.update_website(website_id, data, _owner_id(payload))


@router.delete("/{website_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_website(
    website_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = WebsiteService(db)
    await service.delete_website(website_id, _owner_id(payload))
    return None
