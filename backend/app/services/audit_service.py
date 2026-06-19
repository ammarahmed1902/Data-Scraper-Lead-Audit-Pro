"""Audit orchestration service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditReport, AuditStatus
from app.models.website import WebsiteStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.website_repository import WebsiteRepository
from app.schemas.common import PaginatedResponse
from app.schemas.audit import AuditListResponse


class AuditService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.audit_repo = AuditRepository(session)
        self.website_repo = WebsiteRepository(session)

    async def create_audit(
        self,
        website_id: uuid.UUID,
        created_by: uuid.UUID,
    ) -> AuditReport:
        website = await self.website_repo.get_by_id_for_owner(website_id, created_by)
        if website is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")

        audit = AuditReport(
            website_id=website_id,
            created_by=created_by,
            status=AuditStatus.PENDING.value,
        )
        audit = await self.audit_repo.create(audit)

        website.status = WebsiteStatus.QUEUED.value
        await self.website_repo.update(website)

        from app.workers.tasks import run_audit

        task = run_audit.delay(str(audit.id))
        audit.celery_task_id = task.id
        audit = await self.audit_repo.update(audit)
        return audit

    async def bulk_create_audits(
        self,
        website_ids: list[uuid.UUID],
        created_by: uuid.UUID,
    ) -> list[AuditReport]:
        audits: list[AuditReport] = []
        for website_id in website_ids:
            try:
                audit = await self.create_audit(website_id, created_by)
                audits.append(audit)
            except HTTPException:
                continue
        return audits

    async def get_audit(self, audit_id: uuid.UUID, owner_id: uuid.UUID) -> AuditReport:
        audit = await self.audit_repo.get_with_reports_for_owner(audit_id, owner_id)
        if audit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
        return audit

    async def list_audits(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        website_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> PaginatedResponse[AuditListResponse]:
        skip = (page - 1) * page_size
        audits = await self.audit_repo.list_for_owner(
            owner_id=owner_id,
            skip=skip,
            limit=page_size,
            website_id=website_id,
            status=status,
        )
        total = await self.audit_repo.count_for_owner(
            owner_id=owner_id, website_id=website_id, status=status
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[AuditListResponse.model_validate(a) for a in audits],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def cancel_audit(self, audit_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        audit = await self.audit_repo.get_with_reports_for_owner(audit_id, owner_id)
        if audit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
        if audit.status not in (AuditStatus.PENDING.value, AuditStatus.RUNNING.value):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only pending or running audits can be cancelled",
            )
        audit.status = AuditStatus.CANCELLED.value
        audit.completed_at = datetime.now(timezone.utc)
        await self.audit_repo.update(audit)

    async def get_audit_status(self, audit_id: uuid.UUID, owner_id: uuid.UUID) -> dict:
        audit = await self.get_audit(audit_id, owner_id)
        return {
            "id": str(audit.id),
            "status": audit.status,
            "overall_score": audit.overall_score,
            "error_message": audit.error_message,
            "started_at": audit.started_at,
            "completed_at": audit.completed_at,
        }
