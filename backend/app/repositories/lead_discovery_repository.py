"""Lead discovery repositories."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead_discovery import DiscoveredLead, LeadDiscoverySearch
from app.repositories.base import BaseRepository


class LeadDiscoverySearchRepository(BaseRepository[LeadDiscoverySearch]):
    def __init__(self, session: AsyncSession):
        super().__init__(LeadDiscoverySearch, session)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> list[LeadDiscoverySearch]:
        result = await self.session.execute(
            select(LeadDiscoverySearch)
            .where(LeadDiscoverySearch.user_id == user_id)
            .order_by(LeadDiscoverySearch.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count(LeadDiscoverySearch.id)).where(
                LeadDiscoverySearch.user_id == user_id
            )
        )
        return result.scalar_one()

    async def get_for_user(
        self, search_id: uuid.UUID, user_id: uuid.UUID
    ) -> LeadDiscoverySearch | None:
        result = await self.session.execute(
            select(LeadDiscoverySearch).where(
                LeadDiscoverySearch.id == search_id,
                LeadDiscoverySearch.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class DiscoveredLeadRepository(BaseRepository[DiscoveredLead]):
    def __init__(self, session: AsyncSession):
        super().__init__(DiscoveredLead, session)

    async def list_for_search(
        self,
        search_id: uuid.UUID,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        include_duplicates: bool = False,
    ) -> list[DiscoveredLead]:
        query = select(DiscoveredLead).where(
            DiscoveredLead.search_id == search_id,
            DiscoveredLead.user_id == user_id,
        )
        if not include_duplicates:
            query = query.where(DiscoveredLead.is_duplicate.is_(False))
        query = query.order_by(DiscoveredLead.created_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_for_search(
        self,
        search_id: uuid.UUID,
        user_id: uuid.UUID,
        include_duplicates: bool = False,
    ) -> int:
        query = select(func.count(DiscoveredLead.id)).where(
            DiscoveredLead.search_id == search_id,
            DiscoveredLead.user_id == user_id,
        )
        if not include_duplicates:
            query = query.where(DiscoveredLead.is_duplicate.is_(False))
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_for_user(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> DiscoveredLead | None:
        result = await self.session.execute(
            select(DiscoveredLead).where(
                DiscoveredLead.id == lead_id,
                DiscoveredLead.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_existing_dedup_key(
        self, user_id: uuid.UUID, dedup_key: str
    ) -> DiscoveredLead | None:
        if not dedup_key:
            return None
        result = await self.session.execute(
            select(DiscoveredLead)
            .where(
                DiscoveredLead.user_id == user_id,
                DiscoveredLead.dedup_key == dedup_key,
                DiscoveredLead.is_duplicate.is_(False),
            )
            .order_by(DiscoveredLead.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def dedup_keys_in_search(self, search_id: uuid.UUID) -> set[str]:
        result = await self.session.execute(
            select(DiscoveredLead.dedup_key).where(
                DiscoveredLead.search_id == search_id,
                DiscoveredLead.dedup_key.isnot(None),
            )
        )
        return {row[0] for row in result.all() if row[0]}
