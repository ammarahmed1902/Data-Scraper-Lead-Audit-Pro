"""Lead scoring repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead_discovery import DiscoveredLead
from app.models.lead_scoring import LeadScore, ScoringJob
from app.repositories.base import BaseRepository


class ScoringJobRepository(BaseRepository[ScoringJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(ScoringJob, session)

    async def get_for_user(
        self, job_id: uuid.UUID, user_id: uuid.UUID
    ) -> ScoringJob | None:
        result = await self.session.execute(
            select(ScoringJob).where(
                ScoringJob.id == job_id,
                ScoringJob.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()


class LeadScoreRepository(BaseRepository[LeadScore]):
    def __init__(self, session: AsyncSession):
        super().__init__(LeadScore, session)

    async def get_for_lead(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> LeadScore | None:
        result = await self.session.execute(
            select(LeadScore).where(
                LeadScore.lead_id == lead_id,
                LeadScore.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_ranked(
        self,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20,
        classification: str | None = None,
        search_id: uuid.UUID | None = None,
        min_composite: float | None = None,
        opportunity_category: str | None = None,
    ) -> list[tuple[LeadScore, DiscoveredLead]]:
        query = (
            select(LeadScore, DiscoveredLead)
            .join(DiscoveredLead, LeadScore.lead_id == DiscoveredLead.id)
            .where(
                LeadScore.user_id == user_id,
                DiscoveredLead.is_duplicate.is_(False),
            )
        )
        if classification:
            query = query.where(LeadScore.classification == classification)
        if search_id:
            query = query.where(DiscoveredLead.search_id == search_id)
        if min_composite is not None:
            query = query.where(LeadScore.composite_score >= min_composite)

        query = query.order_by(
            LeadScore.composite_score.desc().nullslast(),
            LeadScore.ranking.asc().nullslast(),
        ).offset(skip).limit(limit)

        result = await self.session.execute(query)
        rows = list(result.all())

        if opportunity_category:
            filtered: list[tuple[LeadScore, DiscoveredLead]] = []
            for score, lead in rows:
                opps = score.opportunities or []
                if any(o.get("category") == opportunity_category for o in opps):
                    filtered.append((score, lead))
            return filtered

        return rows

    async def count_ranked(
        self,
        user_id: uuid.UUID,
        classification: str | None = None,
        search_id: uuid.UUID | None = None,
    ) -> int:
        query = (
            select(func.count(LeadScore.id))
            .join(DiscoveredLead, LeadScore.lead_id == DiscoveredLead.id)
            .where(
                LeadScore.user_id == user_id,
                DiscoveredLead.is_duplicate.is_(False),
            )
        )
        if classification:
            query = query.where(LeadScore.classification == classification)
        if search_id:
            query = query.where(DiscoveredLead.search_id == search_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def dashboard_stats(self, user_id: uuid.UUID) -> dict:
        total = await self.count_ranked(user_id)
        hot = await self.count_ranked(user_id, classification="hot")
        warm = await self.count_ranked(user_id, classification="warm")
        cold = await self.count_ranked(user_id, classification="cold")

        avg_result = await self.session.execute(
            select(func.avg(LeadScore.composite_score)).where(LeadScore.user_id == user_id)
        )
        avg_composite = avg_result.scalar_one()

        return {
            "total_scored": total,
            "hot_leads": hot,
            "warm_leads": warm,
            "cold_leads": cold,
            "average_composite_score": round(float(avg_composite), 1) if avg_composite else None,
        }

    async def get_with_lead(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[LeadScore, DiscoveredLead] | None:
        result = await self.session.execute(
            select(LeadScore, DiscoveredLead)
            .join(DiscoveredLead, LeadScore.lead_id == DiscoveredLead.id)
            .where(LeadScore.lead_id == lead_id, LeadScore.user_id == user_id)
        )
        row = result.one_or_none()
        return row if row else None
