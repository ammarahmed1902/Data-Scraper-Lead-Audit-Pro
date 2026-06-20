"""Lead scoring business logic."""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead_scoring import ScoringJob, ScoringJobStatus, ScoringJobType
from app.repositories.lead_discovery_repository import DiscoveredLeadRepository
from app.repositories.lead_scoring_repository import LeadScoreRepository, ScoringJobRepository
from app.schemas.common import PaginatedResponse
from app.schemas.lead_discovery import DiscoveredLeadResponse
from app.schemas.lead_scoring import (
    LeadScoreResponse,
    OpportunityReportResponse,
    RankedLeadResponse,
    ScoringDashboardResponse,
    ScoringJobResponse,
    ScoringQueuedResponse,
)

logger = structlog.get_logger(__name__)


class LeadScoringService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = ScoringJobRepository(session)
        self.score_repo = LeadScoreRepository(session)
        self.lead_repo = DiscoveredLeadRepository(session)

    async def score_lead(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> ScoringQueuedResponse:
        lead = await self.lead_repo.get_for_user(lead_id, user_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        job = ScoringJob(
            user_id=user_id,
            job_type=ScoringJobType.SINGLE_LEAD.value,
            lead_id=lead_id,
            status=ScoringJobStatus.PENDING.value,
            total_leads=1,
        )
        job = await self.job_repo.create(job)
        await self.session.commit()
        await self._dispatch_job(job)
        return ScoringQueuedResponse(job_id=job.id, status=ScoringJobStatus(job.status))

    async def score_search(
        self, search_id: uuid.UUID, user_id: uuid.UUID
    ) -> ScoringQueuedResponse:
        from app.repositories.lead_discovery_repository import LeadDiscoverySearchRepository

        search_repo = LeadDiscoverySearchRepository(self.session)
        search = await search_repo.get_for_user(search_id, user_id)
        if search is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

        job = ScoringJob(
            user_id=user_id,
            job_type=ScoringJobType.SEARCH_BULK.value,
            search_id=search_id,
            status=ScoringJobStatus.PENDING.value,
        )
        job = await self.job_repo.create(job)
        await self.session.commit()
        await self._dispatch_job(job)
        return ScoringQueuedResponse(job_id=job.id, status=ScoringJobStatus(job.status))

    async def get_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> ScoringJobResponse:
        job = await self.job_repo.get_for_user(job_id, user_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return ScoringJobResponse.model_validate(job)

    async def get_lead_score(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> LeadScoreResponse:
        score = await self.score_repo.get_for_lead(lead_id, user_id)
        if score is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lead has not been scored yet",
            )
        return LeadScoreResponse.model_validate(score)

    async def list_ranked_leads(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        classification: str | None = None,
        search_id: uuid.UUID | None = None,
        min_composite: float | None = None,
        opportunity: str | None = None,
    ) -> PaginatedResponse[RankedLeadResponse]:
        skip = (page - 1) * page_size
        rows = await self.score_repo.list_ranked(
            user_id,
            skip=skip,
            limit=page_size,
            classification=classification,
            search_id=search_id,
            min_composite=min_composite,
            opportunity_category=opportunity,
        )
        total = await self.score_repo.count_ranked(
            user_id, classification=classification, search_id=search_id
        )
        total_pages = max(1, (total + page_size - 1) // page_size)

        items = [
            RankedLeadResponse(
                rank=score.ranking,
                score=LeadScoreResponse.model_validate(score),
                lead=DiscoveredLeadResponse.model_validate(lead),
            )
            for score, lead in rows
        ]
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_dashboard(self, user_id: uuid.UUID) -> ScoringDashboardResponse:
        stats = await self.score_repo.dashboard_stats(user_id)
        hot_rows = await self.score_repo.list_ranked(
            user_id, skip=0, limit=5, classification="hot"
        )
        top_hot = [
            RankedLeadResponse(
                rank=score.ranking,
                score=LeadScoreResponse.model_validate(score),
                lead=DiscoveredLeadResponse.model_validate(lead),
            )
            for score, lead in hot_rows
        ]
        return ScoringDashboardResponse(**stats, top_hot_leads=top_hot)

    async def get_opportunity_report(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> OpportunityReportResponse:
        row = await self.score_repo.get_with_lead(lead_id, user_id)
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scored lead not found",
            )
        score, lead = row
        return OpportunityReportResponse(
            lead_id=lead.id,
            business_name=lead.business_name,
            classification=score.classification,
            composite_score=score.composite_score,
            opportunities=score.opportunities or [],
            opportunity_summary=score.opportunity_summary,
        )

    async def _dispatch_job(self, job: ScoringJob) -> None:
        from app.workers.tasks import run_lead_scoring_job

        try:
            task = run_lead_scoring_job.delay(str(job.id))
            job.celery_task_id = task.id
            await self.job_repo.update(job)
            await self.session.commit()
            logger.info("scoring_job_queued", job_id=str(job.id), celery_task_id=task.id)
        except Exception as exc:
            logger.exception("scoring_queue_failed", job_id=str(job.id))
            job.status = ScoringJobStatus.FAILED.value
            job.error_message = f"Queue dispatch failed: {exc}"[:500]
            await self.job_repo.update(job)
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scoring job created but background worker unavailable.",
            ) from exc
