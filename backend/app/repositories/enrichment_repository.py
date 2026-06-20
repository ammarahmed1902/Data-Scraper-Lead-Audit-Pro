"""Business enrichment repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrichment import BusinessEnrichment, EnrichmentJob
from app.repositories.base import BaseRepository


class EnrichmentJobRepository(BaseRepository[EnrichmentJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(EnrichmentJob, session)

    async def get_for_user(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> EnrichmentJob | None:
        result = await self.session.execute(
            select(EnrichmentJob).where(
                EnrichmentJob.id == job_id,
                EnrichmentJob.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class BusinessEnrichmentRepository(BaseRepository[BusinessEnrichment]):
    def __init__(self, session: AsyncSession):
        super().__init__(BusinessEnrichment, session)

    async def get_for_lead(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> BusinessEnrichment | None:
        result = await self.session.execute(
            select(BusinessEnrichment).where(
                BusinessEnrichment.lead_id == lead_id,
                BusinessEnrichment.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> list[BusinessEnrichment]:
        query = select(BusinessEnrichment).where(BusinessEnrichment.user_id == user_id)
        if status:
            query = query.where(BusinessEnrichment.status == status)
        query = (
            query.order_by(BusinessEnrichment.updated_at.desc()).offset(skip).limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID, status: str | None = None) -> int:
        query = select(func.count(BusinessEnrichment.id)).where(
            BusinessEnrichment.user_id == user_id
        )
        if status:
            query = query.where(BusinessEnrichment.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()
