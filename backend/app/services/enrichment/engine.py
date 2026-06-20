"""Business data enrichment engine — orchestrates crawl, extract, and detect."""

from __future__ import annotations

from typing import Any

import structlog

from app.core.config import settings
from app.services.enrichment.content_extractor import ContentExtractor
from app.services.enrichment.tech_detector import TechStackDetector
from app.services.enrichment.website_crawler import WebsiteCrawler

logger = structlog.get_logger(__name__)


class BusinessEnrichmentEngine:
    """Full enrichment pipeline for a discovered business website."""

    def __init__(self) -> None:
        self.crawler = WebsiteCrawler(
            max_pages=settings.ENRICHMENT_MAX_PAGES,
            request_delay_seconds=settings.ENRICHMENT_REQUEST_DELAY_SECONDS,
        )
        self.extractor = ContentExtractor()
        self.tech_detector = TechStackDetector()

    def enrich(
        self,
        website_url: str,
        fallback_name: str | None = None,
    ) -> dict[str, Any]:
        logger.info("enrichment_engine_start", url=website_url)

        crawl = self.crawler.crawl(website_url)
        if not crawl.pages:
            return {
                "status": "failed",
                "error_message": crawl.errors[0] if crawl.errors else "Could not crawl website",
            }

        home = crawl.get_page("home")
        if not home:
            return {"status": "failed", "error_message": "Homepage unavailable"}

        home_soup = self._soup(home.result.html)
        all_emails: set[str] = set()
        all_phones: set[str] = set()
        services: list[str] = []
        team: list[dict[str, str]] = []
        contact_data: dict[str, Any] = {}
        about_text = ""
        pages_crawled = [p.url for p in crawl.pages]

        for page in crawl.pages:
            if not page.result.html:
                continue
            soup = self._soup(page.result.html)
            html = page.result.html

            all_emails.update(self.extractor.extract_emails(soup, html))
            all_phones.update(self.extractor.extract_phones(soup, html))

            if page.page_type == "about":
                about_text = self.extractor.extract_main_text(soup, max_chars=6000)
            elif page.page_type == "services":
                services.extend(self.extractor.extract_services(soup))
            elif page.page_type == "contact":
                contact_data = self.extractor.extract_contact_data(soup, page.url)
            elif page.page_type == "team":
                team.extend(self.extractor.extract_team_members(soup))

        if not services and home_soup:
            services = self.extractor.extract_services(home_soup)
        if not team and home_soup:
            team = self.extractor.extract_team_members(home_soup)

        company_name = self.extractor.extract_company_name(home_soup, fallback_name)
        meta_desc = self.extractor.extract_meta_description(home_soup)
        business_description = meta_desc or (about_text[:500] if about_text else None)

        if not about_text and home_soup:
            about_text = self.extractor.extract_main_text(home_soup, max_chars=4000)

        tech = self.tech_detector.detect(home.result)

        return {
            "status": "completed",
            "company_name": company_name,
            "about_us_content": about_text or None,
            "services": list(dict.fromkeys(services))[:25] or None,
            "contact_page_data": contact_data or None,
            "email_addresses": sorted(all_emails) or None,
            "phone_numbers": sorted(all_phones) or None,
            "team_members": team[:30] or None,
            "business_description": business_description,
            "technology_stack": tech["technology_stack"],
            "cms_platform": tech["cms_platform"],
            "cms_detected": tech["cms_detected"],
            "pages_crawled": pages_crawled,
            "raw_extraction": {
                "crawl_errors": crawl.errors,
                "homepage_status": home.result.status_code,
            },
        }

    @staticmethod
    def _soup(html: str):
        from bs4 import BeautifulSoup

        return BeautifulSoup(html, "lxml")
