"""Multi-page website crawler for business enrichment."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urljoin, urlparse

import structlog

from app.core.config import settings
from app.services.scraper.page_fetcher import FetchResult, PageFetcher

logger = structlog.get_logger(__name__)

PageType = Literal["home", "about", "services", "contact", "team", "other"]

PAGE_PATTERNS: dict[PageType, re.Pattern[str]] = {
    "about": re.compile(
        r"(about|about-us|about_us|our-story|who-we-are|company)(/|$)",
        re.I,
    ),
    "services": re.compile(
        r"(services|what-we-do|solutions|offerings|practice-areas)(/|$)",
        re.I,
    ),
    "contact": re.compile(
        r"(contact|contact-us|contact_us|get-in-touch|reach-us)(/|$)",
        re.I,
    ),
    "team": re.compile(
        r"(team|our-team|staff|leadership|people|meet-the-team)(/|$)",
        re.I,
    ),
}


@dataclass
class CrawledPage:
    url: str
    page_type: PageType
    result: FetchResult


@dataclass
class CrawlResult:
    base_url: str
    pages: list[CrawledPage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def get_page(self, page_type: PageType) -> CrawledPage | None:
        for page in self.pages:
            if page.page_type == page_type:
                return page
        return None


class WebsiteCrawler:
    """Crawl homepage and key business pages within the same domain."""

    def __init__(
        self,
        fetcher: PageFetcher | None = None,
        max_pages: int = 6,
        request_delay_seconds: float = 0.5,
    ):
        self.fetcher = fetcher or PageFetcher(
            timeout=settings.ENRICHMENT_FETCH_TIMEOUT_SECONDS,
            max_retries=2,
        )
        self.max_pages = max_pages
        self.request_delay_seconds = request_delay_seconds
        self._last_fetch_at = 0.0

    def crawl(self, start_url: str) -> CrawlResult:
        parsed = urlparse(start_url if "://" in start_url else f"https://{start_url}")
        base = f"{parsed.scheme}://{parsed.netloc}"
        result = CrawlResult(base_url=base)

        home = self._fetch_typed(base, "home")
        if home.result.error or home.result.status_code >= 400:
            result.errors.append(home.result.error or f"HTTP {home.result.status_code}")
            return result

        result.pages.append(home)
        candidates = self._discover_links(home.result, base)
        fetched_types: set[PageType] = {"home"}

        for page_type in ("about", "services", "contact", "team"):
            if page_type in fetched_types:
                continue
            url = candidates.get(page_type)
            if not url:
                continue
            page = self._fetch_typed(url, page_type)
            if page.result.status_code < 400 and page.result.html:
                result.pages.append(page)
                fetched_types.add(page_type)
            if len(result.pages) >= self.max_pages:
                break

        return result

    def _discover_links(self, home: FetchResult, base: str) -> dict[PageType, str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(home.html, "lxml")
        base_host = urlparse(base).netloc
        found: dict[PageType, str] = {}

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if href.startswith(("#", "javascript:", "mailto:", "tel:")):
                continue
            absolute = urljoin(home.final_url, href)
            link_host = urlparse(absolute).netloc
            if link_host and link_host != base_host:
                continue
            path = urlparse(absolute).path
            for page_type, pattern in PAGE_PATTERNS.items():
                if page_type not in found and pattern.search(path):
                    found[page_type] = absolute
        return found

    def _fetch_typed(self, url: str, page_type: PageType) -> CrawledPage:
        elapsed = time.monotonic() - self._last_fetch_at
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        fetch_result = self.fetcher.fetch(url)
        self._last_fetch_at = time.monotonic()
        logger.debug("enrichment_crawled_page", url=url, type=page_type, status=fetch_result.status_code)
        return CrawledPage(url=url, page_type=page_type, result=fetch_result)
