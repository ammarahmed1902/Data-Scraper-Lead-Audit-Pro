"""Report repository."""

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditReport
from app.models.report import Report
from app.models.website import Website
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, session: AsyncSession):
        super().__init__(Report, session)

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        audit_id: uuid.UUID | None = None,
    ) -> List[Report]:
        query = (
            select(Report)
            .join(AuditReport, Report.audit_report_id == AuditReport.id)
            .join(Website, AuditReport.website_id == Website.id)
            .where(Website.owner_id == owner_id)
        )
        if audit_id:
            query = query.where(Report.audit_report_id == audit_id)
        query = query.order_by(Report.generated_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_owner(
        self, owner_id: uuid.UUID, audit_id: uuid.UUID | None = None
    ) -> int:
        query = (
            select(func.count())
            .select_from(Report)
            .join(AuditReport, Report.audit_report_id == AuditReport.id)
            .join(Website, AuditReport.website_id == Website.id)
            .where(Website.owner_id == owner_id)
        )
        if audit_id:
            query = query.where(Report.audit_report_id == audit_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_for_owner(self, report_id: uuid.UUID, owner_id: uuid.UUID) -> Optional[Report]:
        result = await self.session.execute(
            select(Report)
            .join(AuditReport, Report.audit_report_id == AuditReport.id)
            .join(Website, AuditReport.website_id == Website.id)
            .where(Report.id == report_id, Website.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_audit_for_owner(
        self, audit_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Optional[AuditReport]:
        result = await self.session.execute(
            select(AuditReport)
            .join(Website, AuditReport.website_id == Website.id)
            .options(
                selectinload(AuditReport.seo_report),
                selectinload(AuditReport.performance_report),
                selectinload(AuditReport.technical_report),
            )
            .where(AuditReport.id == audit_id, Website.owner_id == owner_id)
        )
        return result.scalar_one_or_none()

    async def get_expired(self) -> List[Report]:
        from datetime import datetime, timezone

        result = await self.session.execute(
            select(Report).where(
                Report.expires_at.isnot(None),
                Report.expires_at < datetime.now(timezone.utc),
            )
        )
        return list(result.scalars().all())
