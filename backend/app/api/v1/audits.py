"""
Audit management endpoints.
"""

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.audit import AuditBulkCreate, AuditCreate, AuditListResponse, AuditResponse
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService

router = APIRouter()


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("", response_model=PaginatedResponse[AuditListResponse])
async def list_audits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    website_id: uuid.UUID | None = None,
    status_filter: str | None = Query(None, alias="status"),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    return await service.list_audits(
        owner_id=_user_id(payload),
        page=page,
        page_size=page_size,
        website_id=website_id,
        status=status_filter,
    )


@router.get("/{audit_id}", response_model=AuditResponse)
async def get_audit(
    audit_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    audit = await service.get_audit(audit_id, _user_id(payload))
    return AuditResponse.model_validate(audit)


@router.post("", response_model=AuditResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_audit(
    data: AuditCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    audit = await service.create_audit(data.website_id, _user_id(payload))
    return AuditResponse.model_validate(audit)


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def bulk_create_audits(
    data: AuditBulkCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    audits = await service.bulk_create_audits(data.website_ids, _user_id(payload))
    return {"queued": len(audits), "audit_ids": [str(a.id) for a in audits]}


@router.delete("/{audit_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_audit(
    audit_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    await service.cancel_audit(audit_id, _user_id(payload))
    return None


@router.get("/{audit_id}/status")
async def get_audit_status(
    audit_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    return await service.get_audit_status(audit_id, _user_id(payload))
