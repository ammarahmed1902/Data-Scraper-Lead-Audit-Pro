"""Audit repository."""

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditReport
from app.models.website import Website
from app.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditReport]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditReport, session)

    async def get_with_reports(self, audit_id: uuid.UUID) -> Optional[AuditReport]:
        result = await self.session.execute(
            select(AuditReport)
            .options(
                selectinload(AuditReport.seo_report),
                selectinload(AuditReport.performance_report),
                selectinload(AuditReport.technical_report),
            )
            .where(AuditReport.id == audit_id)
        )
        return result.scalar_one_or_none()

    async def get_with_reports_for_owner(
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

    def _owner_filter(self, owner_id: uuid.UUID, website_id: uuid.UUID | None, status: str | None):
        query = select(AuditReport).join(Website, AuditReport.website_id == Website.id).where(
            Website.owner_id == owner_id
        )
        if website_id:
            query = query.where(AuditReport.website_id == website_id)
        if status:
            query = query.where(AuditReport.status == status)
        return query

    async def list_for_owner(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        website_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> List[AuditReport]:
        query = (
            self._owner_filter(owner_id, website_id, status)
            .order_by(AuditReport.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_owner(
        self,
        owner_id: uuid.UUID,
        website_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> int:
        query = select(func.count(AuditReport.id)).join(
            Website, AuditReport.website_id == Website.id
        ).where(Website.owner_id == owner_id)
        if website_id:
            query = query.where(AuditReport.website_id == website_id)
        if status:
            query = query.where(AuditReport.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_website(
        self,
        website_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[AuditReport]:
        result = await self.session.execute(
            select(AuditReport)
            .where(AuditReport.website_id == website_id)
            .offset(skip)
            .limit(limit)
            .order_by(AuditReport.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str, limit: int = 100) -> List[AuditReport]:
        result = await self.session.execute(
            select(AuditReport)
            .where(AuditReport.status == status)
            .limit(limit)
            .order_by(AuditReport.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_failed_for_retry(self, max_retries: int, limit: int = 50) -> List[AuditReport]:
        result = await self.session.execute(
            select(AuditReport)
            .where(AuditReport.status == "failed")
            .limit(limit)
            .order_by(AuditReport.created_at.asc())
        )
        audits = list(result.scalars().all())
        return [
            a
            for a in audits
            if (a.raw_data or {}).get("retry_count", 0) < max_retries
        ]
