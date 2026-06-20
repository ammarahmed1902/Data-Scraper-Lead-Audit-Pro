"""Synchronous lead discovery runner for Celery workers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.lead_discovery import DiscoveredLead, DiscoverySearchStatus, LeadDiscoverySearch
from app.services.discovery.engine import LeadDiscoveryEngine

logger = structlog.get_logger(__name__)


class LeadDiscoveryRunner:
    def __init__(self, session: Session):
        self.session = session
        self.engine = LeadDiscoveryEngine()

    def run(self, search_id: uuid.UUID) -> LeadDiscoverySearch:
        search = self.session.get(LeadDiscoverySearch, search_id)
        if search is None:
            raise ValueError(f"Discovery search {search_id} not found")

        if search.status in (
            DiscoverySearchStatus.COMPLETED.value,
            DiscoverySearchStatus.CANCELLED.value,
        ):
            return search

        search.status = DiscoverySearchStatus.RUNNING.value
        search.started_at = datetime.now(UTC)
        search.error_message = None
        self.session.flush()

        logger.info(
            "discovery_runner_start",
            search_id=str(search_id),
            source_category=search.data_source_category,
            source_website=search.data_source_website,
            source_search_url=search.source_search_url,
            industry=search.industry_keyword,
            country=search.country,
            state=search.state,
            city=search.city,
        )

        existing_user_keys = self._load_user_dedup_keys(search.user_id)
        search_keys = self._load_search_dedup_keys(search.id)

        page = 1
        max_pages = settings.DISCOVERY_MAX_PAGES_PER_SEARCH
        scrape_stats: dict[str, int] = {"success": 0, "partial": 0, "failed": 0, "skipped": 0}

        try:
            while page <= max_pages:
                leads, has_more = self.engine.discover_page(
                    industry_keyword=search.industry_keyword,
                    country=search.country,
                    state=search.state,
                    city=search.city,
                    page=page,
                    page_size=settings.DISCOVERY_PAGE_SIZE,
                    data_source_category=search.data_source_category,
                    data_source_website=search.data_source_website,
                )

                for lead_data in leads:
                    dedup_key = lead_data.get("dedup_key")
                    is_dup = False
                    duplicate_of_id = None

                    if dedup_key in search_keys:
                        is_dup = True
                    elif dedup_key in existing_user_keys:
                        is_dup = True
                        duplicate_of_id = existing_user_keys.get(dedup_key)

                    record = DiscoveredLead(
                        search_id=search.id,
                        user_id=search.user_id,
                        business_name=lead_data["business_name"],
                        website_url=lead_data.get("website_url"),
                        domain=lead_data.get("domain"),
                        business_category=lead_data.get("business_category"),
                        address=lead_data.get("address"),
                        city=lead_data.get("city"),
                        state=lead_data.get("state"),
                        country=lead_data.get("country"),
                        phone_number=lead_data.get("phone_number"),
                        email_address=lead_data.get("email_address"),
                        social_profiles=lead_data.get("social_profiles"),
                        source=lead_data.get("source"),
                        profile_url=lead_data.get("profile_url"),
                        scrape_status=lead_data.get("scrape_status"),
                        scrape_errors=lead_data.get("scrape_errors"),
                        dedup_key=dedup_key,
                        is_duplicate=is_dup,
                        duplicate_of_id=duplicate_of_id,
                        raw_data=lead_data.get("raw_data"),
                    )
                    self.session.add(record)
                    self.session.flush()

                    scrape_status = lead_data.get("scrape_status")
                    if scrape_status in scrape_stats:
                        scrape_stats[scrape_status] += 1

                    search.total_found += 1
                    if is_dup:
                        search.total_duplicates += 1
                    else:
                        search.total_new += 1
                        if dedup_key:
                            search_keys.add(dedup_key)
                            existing_user_keys[dedup_key] = record.id

                search.pages_processed = page
                self.session.flush()

                if not has_more or not leads:
                    break
                page += 1

            search.status = DiscoverySearchStatus.COMPLETED.value
            search.completed_at = datetime.now(UTC)
            logger.info(
                "discovery_search_completed",
                search_id=str(search_id),
                total_found=search.total_found,
                total_new=search.total_new,
                total_duplicates=search.total_duplicates,
                total_failed=scrape_stats.get("failed", 0),
                scrape_stats=scrape_stats,
                pages_processed=search.pages_processed,
            )
        except Exception as exc:
            error_detail = str(exc)[:2000]
            logger.exception(
                "discovery_search_failed",
                search_id=str(search_id),
                error_type=type(exc).__name__,
                error=error_detail,
            )
            search.status = DiscoverySearchStatus.FAILED.value
            search.error_message = error_detail
            search.completed_at = datetime.now(UTC)

        self.session.flush()
        return search

    def _load_user_dedup_keys(self, user_id: uuid.UUID) -> dict[str, uuid.UUID]:
        rows = (
            self.session.query(DiscoveredLead.dedup_key, DiscoveredLead.id)
            .filter(
                DiscoveredLead.user_id == user_id,
                DiscoveredLead.is_duplicate.is_(False),
                DiscoveredLead.dedup_key.isnot(None),
            )
            .all()
        )
        return {row[0]: row[1] for row in rows if row[0]}

    def _load_search_dedup_keys(self, search_id: uuid.UUID) -> set[str]:
        rows = (
            self.session.query(DiscoveredLead.dedup_key)
            .filter(
                DiscoveredLead.search_id == search_id,
                DiscoveredLead.dedup_key.isnot(None),
            )
            .all()
        )
        return {row[0] for row in rows if row[0]}
