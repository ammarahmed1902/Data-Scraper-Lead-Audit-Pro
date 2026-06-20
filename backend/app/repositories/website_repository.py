"""Website repository."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.website import Website
from app.repositories.base import BaseRepository


class WebsiteRepository(BaseRepository[Website]):
    def __init__(self, session: AsyncSession):
        super().__init__(Website, session)

    def _apply_filters(
        self,
        query,
        owner_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
    ):
        query = query.where(Website.owner_id == owner_id)
        if status:
            query = query.where(Website.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.where(
                or_(
                    Website.url.ilike(pattern),
                    Website.domain.ilike(pattern),
                    Website.company_name.ilike(pattern),
                    Website.contact_name.ilike(pattern),
                    Website.contact_email.ilike(pattern),
                )
            )
        return query

    async def get_by_owner(
        self,
        owner_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> list[Website]:
        query = select(Website)
        query = self._apply_filters(query, owner_id, status, search)
        query = query.order_by(Website.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_owner(
        self,
        owner_id: uuid.UUID,
        status: str | None = None,
        search: str | None = None,
    ) -> int:
        query = select(func.count()).select_from(Website)
        query = self._apply_filters(query, owner_id, status, search)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_by_id_for_owner(
        self, website_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Website | None:
        result = await self.session.execute(
            select(Website).where(
                Website.id == website_id,
                Website.owner_id == owner_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str, owner_id: uuid.UUID) -> Website | None:
        result = await self.session.execute(
            select(Website).where(Website.domain == domain, Website.owner_id == owner_id)
        )
        return result.scalar_one_or_none()
