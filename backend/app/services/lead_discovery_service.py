"""Lead discovery business logic."""

from __future__ import annotations

import threading
import uuid

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead_discovery import DiscoveredLead, DiscoverySearchStatus, LeadDiscoverySearch
from app.repositories.lead_discovery_repository import (
    DiscoveredLeadRepository,
    LeadDiscoverySearchRepository,
)
from app.schemas.common import PaginatedResponse
from app.schemas.lead_discovery import (
    DiscoveredLeadResponse,
    DiscoverySearchCreate,
    DiscoverySearchListResponse,
    DiscoverySearchResponse,
)
from app.schemas.website import WebsiteCreate
from app.services.discovery.source_urls import build_source_search_url
from app.services.website_service import WebsiteService

logger = structlog.get_logger(__name__)


class LeadDiscoveryService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.search_repo = LeadDiscoverySearchRepository(session)
        self.lead_repo = DiscoveredLeadRepository(session)

    async def create_search(
        self, data: DiscoverySearchCreate, user_id: uuid.UUID
    ) -> LeadDiscoverySearch:
        logger.info(
            "discovery_create_search",
            user_id=str(user_id),
            source_category=data.data_source_category,
            source_website=data.data_source_website,
            industry=data.industry_keyword,
            country=data.country,
            state=data.state,
            city=data.city,
        )

        source_search_url = (
            build_source_search_url(
                category=data.data_source_category,
                website=data.data_source_website,
                industry_keyword=data.industry_keyword,
                country=data.country,
                state=data.state,
                city=data.city,
            )
            if data.data_source_category and data.data_source_website
            else None
        )
        logger.info(
            "discovery_search_url_built",
            source_search_url=source_search_url,
        )

        search = LeadDiscoverySearch(
            user_id=user_id,
            industry_keyword=data.industry_keyword,
            country=data.country,
            state=data.state,
            city=data.city,
            data_source_category=data.data_source_category,
            data_source_website=data.data_source_website,
            source_search_url=source_search_url,
            status=DiscoverySearchStatus.PENDING.value,
        )
        search = await self.search_repo.create(search)
        await self.session.commit()
        search_id = search.id

        from app.workers.tasks import run_discovery_search

        if settings.CELERY_TASK_ALWAYS_EAGER:
            self._start_discovery_background(search_id)
            logger.info("discovery_search_started_inline", search_id=str(search_id))
        else:
            try:
                task = run_discovery_search.delay(str(search_id))
                search.celery_task_id = task.id
                search = await self.search_repo.update(search)
                await self.session.commit()
                logger.info(
                    "discovery_search_queued",
                    search_id=str(search_id),
                    celery_task_id=task.id,
                )
            except Exception as exc:
                error_detail = str(exc)[:500]
                logger.exception(
                    "discovery_queue_failed",
                    search_id=str(search_id),
                    error_type=type(exc).__name__,
                    error=error_detail,
                )
                search.status = DiscoverySearchStatus.FAILED.value
                search.error_message = f"Queue dispatch failed: {error_detail}"
                await self.search_repo.update(search)
                await self.session.commit()
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Discovery background task failed to start: {error_detail}",
                ) from exc

        return search

    @staticmethod
    def _start_discovery_background(search_id: uuid.UUID) -> None:
        """Run discovery in a daemon thread so API requests return immediately."""

        def _run() -> None:
            try:
                from app.core.sync_database import get_sync_session
                from app.services.discovery_runner import LeadDiscoveryRunner

                with get_sync_session() as sync_session:
                    LeadDiscoveryRunner(sync_session).run(search_id)
            except Exception:
                logger.exception(
                    "discovery_inline_background_failed",
                    search_id=str(search_id),
                )

        threading.Thread(target=_run, daemon=True, name=f"discovery-{search_id}").start()

    async def get_search(
        self, search_id: uuid.UUID, user_id: uuid.UUID
    ) -> DiscoverySearchResponse:
        search = await self.search_repo.get_for_user(search_id, user_id)
        if search is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")
        return DiscoverySearchResponse.model_validate(search)

    async def list_searches(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[DiscoverySearchListResponse]:
        skip = (page - 1) * page_size
        searches = await self.search_repo.list_for_user(user_id, skip=skip, limit=page_size)
        total = await self.search_repo.count_for_user(user_id)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[DiscoverySearchListResponse.model_validate(s) for s in searches],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def list_leads(
        self,
        search_id: uuid.UUID,
        user_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        include_duplicates: bool = False,
    ) -> PaginatedResponse[DiscoveredLeadResponse]:
        search = await self.search_repo.get_for_user(search_id, user_id)
        if search is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found")

        skip = (page - 1) * page_size
        leads = await self.lead_repo.list_for_search(
            search_id, user_id, skip=skip, limit=page_size, include_duplicates=include_duplicates
        )
        total = await self.lead_repo.count_for_search(
            search_id, user_id, include_duplicates=include_duplicates
        )
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[DiscoveredLeadResponse.model_validate(lead) for lead in leads],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def import_lead_to_website(
        self, lead_id: uuid.UUID, user_id: uuid.UUID
    ) -> tuple[DiscoveredLead, uuid.UUID]:
        lead = await self.lead_repo.get_for_user(lead_id, user_id)
        if lead is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
        if lead.imported_website_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Lead already imported to websites",
            )
        if not lead.website_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead has no website URL to import",
            )

        website_service = WebsiteService(self.session)
        website = await website_service.create_website(
            WebsiteCreate(
                url=lead.website_url,
                company_name=lead.business_name,
                contact_email=lead.email_address,
                contact_phone=lead.phone_number,
                industry=lead.business_category,
            ),
            user_id,
        )
        lead.imported_website_id = uuid.UUID(str(website.id))
        await self.lead_repo.update(lead)
        logger.info(
            "discovery_lead_imported",
            lead_id=str(lead_id),
            website_id=str(website.id),
        )
        return lead, uuid.UUID(str(website.id))
