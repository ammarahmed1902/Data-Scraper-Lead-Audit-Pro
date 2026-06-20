"""Business enrichment business logic."""

from __future__ import annotations

import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrichment import (
    EnrichmentJob,
    EnrichmentJobType,
    EnrichmentStatus,
)
from app.repositories.enrichment_repository import (
    BusinessEnrichmentRepository,
    EnrichmentJobRepository,
)
from app.repositories.lead_discovery_repository import (
    DiscoveredLeadRepository,
    LeadDiscoverySearchRepository,
)
from app.schemas.common import PaginatedResponse
from app.schemas.enrichment import (
    BusinessEnrichmentListResponse,
    BusinessEnrichmentResponse,
    EnrichmentJobResponse,
    EnrichmentQueuedResponse,
)

logger = structlog.get_logger(__name__)


class EnrichmentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.job_repo = EnrichmentJobRepository(session)
        self.enrichment_repo = BusinessEnrichmentRepository(session)
        self.lead_repo = DiscoveredLeadRepository(session)
        self.search_repo = LeadDiscoverySearchRepository(session)

    async def enrich_lead(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> EnrichmentQueuedResponse:
        lead = await self.lead_repo.get_for_user(lead_id, user_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        if not lead.website_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead has no website URL to enrich",
            )

        job = EnrichmentJob(
            user_id=user_id,
            job_type=EnrichmentJobType.SINGLE_LEAD.value,
            lead_id=lead_id,
            status=EnrichmentStatus.PENDING.value,
            total_leads=1,
        )
        job = await self.job_repo.create(job)
        await self.session.commit()

        await self._dispatch_job(job)
        return EnrichmentQueuedResponse(job_id=job.id, status=EnrichmentStatus(job.status))

    async def enrich_search(
        self, search_id: uuid.UUID, user_id: uuid.UUID
    ) -> EnrichmentQueuedResponse:
        search = await self.search_repo.get_for_user(search_id, user_id)
        if search is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

        leads = await self.lead_repo.list_for_search(
            search_id, user_id, skip=0, limit=10000, include_duplicates=False
        )
        enrichable = [lead for lead in leads if lead.website_url]
        if not enrichable:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No leads with websites found for this search",
            )

        job = EnrichmentJob(
            user_id=user_id,
            job_type=EnrichmentJobType.SEARCH_BULK.value,
            search_id=search_id,
            status=EnrichmentStatus.PENDING.value,
            total_leads=len(enrichable),
        )
        job = await self.job_repo.create(job)
        await self.session.commit()

        await self._dispatch_job(job)
        return EnrichmentQueuedResponse(job_id=job.id, status=EnrichmentStatus(job.status))

    async def get_job(self, job_id: uuid.UUID, user_id: uuid.UUID) -> EnrichmentJobResponse:
        job = await self.job_repo.get_for_user(job_id, user_id)
        if job is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return EnrichmentJobResponse.model_validate(job)

    async def get_lead_enrichment(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> BusinessEnrichmentResponse:
        lead = await self.lead_repo.get_for_user(lead_id, user_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")

        enrichment = await self.enrichment_repo.get_for_lead(lead_id, user_id)
        if enrichment is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No enrichment data for this lead",
            )
        return BusinessEnrichmentResponse.model_validate(enrichment)

    async def list_enrichments(
        self,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status_filter: str | None = None,
    ) -> PaginatedResponse[BusinessEnrichmentListResponse]:
        skip = (page - 1) * page_size
        items = await self.enrichment_repo.list_for_user(
            user_id, skip=skip, limit=page_size, status=status_filter
        )
        total = await self.enrichment_repo.count_for_user(user_id, status=status_filter)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[BusinessEnrichmentListResponse.model_validate(e) for e in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def _dispatch_job(self, job: EnrichmentJob) -> None:
        from app.workers.tasks import run_enrichment_job

        try:
            task = run_enrichment_job.delay(str(job.id))
            job.celery_task_id = task.id
            await self.job_repo.update(job)
            await self.session.commit()
            logger.info(
                "enrichment_job_queued",
                job_id=str(job.id),
                celery_task_id=task.id,
            )
        except Exception as exc:
            logger.exception("enrichment_queue_failed", job_id=str(job.id))
            job.status = EnrichmentStatus.FAILED.value
            job.error_message = f"Queue dispatch failed: {exc}"[:500]
            await self.job_repo.update(job)
            await self.session.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Enrichment job created but background worker unavailable.",
            ) from exc
