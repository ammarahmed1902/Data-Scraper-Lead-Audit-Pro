"""
Audit management endpoints.
"""

import uuid

import structlog
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.audit import (
    AuditBulkCreate,
    AuditCreate,
    AuditLeadCreate,
    AuditListResponse,
    AuditResponse,
    to_audit_response,
)
from app.schemas.common import PaginatedResponse
from app.services.audit_service import AuditService

router = APIRouter()
logger = structlog.get_logger(__name__)


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
    return to_audit_response(audit, include_reports=True)


@router.post("", response_model=AuditResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_audit(
    data: AuditCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    logger.info(
        "audit_api_create_request",
        website_id=str(data.website_id),
        user_id=str(user_id),
    )
    service = AuditService(db)
    audit = await service.create_audit(data.website_id, user_id)
    response = to_audit_response(audit, include_reports=False)
    logger.info(
        "audit_api_create_response",
        audit_id=str(audit.id),
        status=audit.status,
        celery_task_id=audit.celery_task_id,
    )
    return response


@router.post("/bulk", status_code=status.HTTP_202_ACCEPTED)
async def bulk_create_audits(
    data: AuditBulkCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = AuditService(db)
    audits = await service.bulk_create_audits(data.website_ids, _user_id(payload))
    return {"queued": len(audits), "audit_ids": [str(a.id) for a in audits]}


@router.post(
    "/leads/{lead_id}",
    response_model=AuditResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_audit_for_lead(
    lead_id: uuid.UUID,
    data: AuditLeadCreate | None = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    user_id = _user_id(payload)
    logger.info("audit_api_lead", lead_id=str(lead_id), user_id=str(user_id))
    service = AuditService(db)
    audit = await service.create_audit_for_lead(
        lead_id,
        user_id,
        auto_import=data.auto_import if data else True,
    )
    return to_audit_response(audit, include_reports=False)


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
