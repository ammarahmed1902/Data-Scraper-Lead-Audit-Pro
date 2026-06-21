"""Audit orchestration service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditReport, AuditStatus
from app.models.website import WebsiteStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.website_repository import WebsiteRepository
from app.schemas.audit import AuditListResponse, to_audit_list_response
from app.schemas.common import PaginatedResponse

logger = structlog.get_logger(__name__)


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
        logger.info(
            "audit_create_start",
            website_id=str(website_id),
            created_by=str(created_by),
        )

        website = await self.website_repo.get_by_id_for_owner(website_id, created_by)
        if website is None:
            logger.warning(
                "audit_create_website_not_found",
                website_id=str(website_id),
                created_by=str(created_by),
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Website not found")

        audit = AuditReport(
            website_id=website_id,
            created_by=created_by,
            status=AuditStatus.PENDING.value,
        )
        audit = await self.audit_repo.create(audit)
        logger.info("audit_record_created", audit_id=str(audit.id), website_id=str(website_id))

        website.status = WebsiteStatus.QUEUED.value
        await self.website_repo.update(website)

        # Commit before queue dispatch so Celery (including eager mode) can read the row.
        await self.session.commit()
        logger.info("audit_create_committed", audit_id=str(audit.id))

        from app.workers.tasks import run_audit

        try:
            task = run_audit.delay(str(audit.id))
            audit.celery_task_id = task.id
            audit = await self.audit_repo.update(audit)
            await self.session.commit()
            logger.info(
                "audit_queued",
                audit_id=str(audit.id),
                celery_task_id=task.id,
            )
        except Exception as exc:
            logger.exception(
                "audit_queue_dispatch_failed",
                audit_id=str(audit.id),
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Audit created but queue dispatch failed. Ensure Redis/Celery is running.",
            ) from exc

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

    async def create_audit_for_lead(
        self,
        lead_id: uuid.UUID,
        created_by: uuid.UUID,
        auto_import: bool = True,
    ) -> AuditReport:
        """Import discovered lead to websites (if needed) and queue an audit."""
        from app.repositories.lead_discovery_repository import DiscoveredLeadRepository
        from app.services.lead_discovery_service import LeadDiscoveryService

        lead_repo = DiscoveredLeadRepository(self.session)
        lead = await lead_repo.get_for_user(lead_id, created_by)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        if not lead.website_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead has no website URL to audit",
            )

        website_id = lead.imported_website_id
        if website_id is None:
            if not auto_import:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Lead not imported — import first or set auto_import=true",
                )
            discovery = LeadDiscoveryService(self.session)
            _, website_id = await discovery.import_lead_to_website(lead_id, created_by)
            await self.session.commit()

        return await self.create_audit(website_id, created_by)

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
            items=[to_audit_list_response(a) for a in audits],
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
        audit.completed_at = datetime.now(UTC)
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
