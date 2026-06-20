"""Lead discovery engine orchestrator."""

from __future__ import annotations

from typing import Any

import structlog

from app.core.config import settings
from app.models.lead_discovery import DiscoverySourceCategory
from app.services.discovery.dedup import build_dedup_key, domain_from_url
from app.services.discovery.enrichment import LeadEnrichmentService
from app.services.discovery.extraction_utils import is_platform_listing_url
from app.services.discovery.providers.directory_provider import DirectorySearchProvider
from app.services.discovery.providers.osm_provider import OSMBusinessProvider
from app.services.discovery.providers.web_search_provider import WebSearchProvider

logger = structlog.get_logger(__name__)


class LeadDiscoveryEngine:
    """Coordinates public data providers, enrichment, and deduplication."""

    def __init__(self) -> None:
        ua = settings.DISCOVERY_USER_AGENT
        delay = settings.DISCOVERY_REQUEST_DELAY_SECONDS
        self.osm = OSMBusinessProvider(
            user_agent=ua,
            request_delay_seconds=delay,
            max_results=settings.DISCOVERY_MAX_RESULTS_PER_SEARCH,
        )
        self.web = WebSearchProvider(user_agent=ua, request_delay_seconds=delay * 2)
        self.directory = DirectorySearchProvider(
            user_agent=ua, request_delay_seconds=delay
        )
        self.enrichment = LeadEnrichmentService(user_agent=ua, request_delay_seconds=delay)

    def discover_page(
        self,
        *,
        industry_keyword: str,
        country: str,
        state: str | None,
        city: str | None,
        page: int,
        page_size: int = 50,
        data_source_category: str | None = None,
        data_source_website: str | None = None,
    ) -> tuple[list[dict[str, Any]], bool]:
        logger.info(
            "discovery_page_start",
            industry=industry_keyword,
            country=country,
            state=state,
            city=city,
            page=page,
            source_category=data_source_category,
            source_website=data_source_website,
        )

        directory_leads: list[dict[str, Any]] = []
        if page == 1 and data_source_category and data_source_website:
            directory_leads = self.directory.discover(
                category=data_source_category,
                website=data_source_website,
                industry_keyword=industry_keyword,
                country=country,
                state=state,
                city=city,
                page=page,
            )

        osm_leads: list[dict[str, Any]] = []
        osm_has_more = False
        if not directory_leads or data_source_category is None:
            osm_leads, osm_has_more = self.osm.discover(
                industry_keyword=industry_keyword,
                country=country,
                state=state,
                city=city,
                page=page,
                page_size=page_size,
            )

        web_leads: list[dict[str, Any]] = []
        if page == 1 and (
            not directory_leads
            or data_source_category == DiscoverySourceCategory.BUSINESS_DIRECTORY.value
        ):
            web_leads = self.web.discover(
                industry_keyword=industry_keyword,
                country=country,
                state=state,
                city=city,
                page=1,
            )

        merged = self._merge_leads(directory_leads + osm_leads + web_leads)
        enriched: list[dict[str, Any]] = []
        for lead in merged:
            website = lead.get("website_url")
            if (
                website
                and settings.DISCOVERY_ENRICH_WEBSITES
                and not is_platform_listing_url(website)
            ):
                lead = self.enrichment.enrich(lead)
            domain = domain_from_url(lead.get("website_url"))
            lead["domain"] = domain
            lead["dedup_key"] = build_dedup_key(
                business_name=lead["business_name"],
                domain=domain,
                phone=lead.get("phone_number"),
                city=lead.get("city"),
            )
            enriched.append(lead)

        has_more = osm_has_more or (page == 1 and len(web_leads) >= 10)
        logger.info(
            "discovery_page_complete",
            page=page,
            count=len(enriched),
            has_more=has_more,
        )
        return enriched, has_more

    @staticmethod
    def _merge_leads(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        merged: list[dict[str, Any]] = []
        seen: set[str] = set()
        for lead in leads:
            domain = domain_from_url(lead.get("website_url"))
            key = domain or lead.get("business_name", "").lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(lead)
        return merged
