"""DuckDuckGo HTML search provider for supplemental business discovery."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger(__name__)

DDG_HTML_URL = "https://html.duckduckgo.com/html/"


class WebSearchProvider:
    """Supplement OSM results with public search result snippets."""

    def __init__(self, user_agent: str, request_delay_seconds: float = 2.0):
        self.user_agent = user_agent
        self.request_delay_seconds = request_delay_seconds
        self._last_request_at = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def discover(
        self,
        *,
        industry_keyword: str,
        country: str,
        state: str | None,
        city: str | None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        location_parts = [p for p in (city, state, country) if p]
        location = " ".join(location_parts)
        query = f"{industry_keyword} {location} business"

        self._rate_limit()
        try:
            with httpx.Client(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = client.post(
                    DDG_HTML_URL,
                    data={"q": query, "s": str((page - 1) * 30)},
                )
                response.raise_for_status()
                html = response.text
        except Exception as exc:
            logger.warning("web_search_failed", query=query, error=str(exc))
            return []

        soup = BeautifulSoup(html, "lxml")
        leads: list[dict[str, Any]] = []

        for result in soup.select(".result"):
            title_el = result.select_one(".result__title")
            snippet_el = result.select_one(".result__snippet")
            link_el = result.select_one("a.result__a")
            if not title_el or not link_el:
                continue

            name = title_el.get_text(strip=True)
            href = link_el.get("href", "")
            website = self._resolve_ddg_url(href)
            if not name:
                continue

            phone = None
            email = None
            if snippet_el:
                snippet = snippet_el.get_text(" ", strip=True)
                phone_match = re.search(
                    r"(\+?\d[\d\s().-]{8,}\d)", snippet
                )
                if phone_match:
                    phone = phone_match.group(1)
                email_match = re.search(
                    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
                    snippet,
                )
                if email_match:
                    email = email_match.group(0).lower()

            leads.append(
                {
                    "business_name": name[:500],
                    "website_url": website,
                    "business_category": industry_keyword,
                    "address": None,
                    "city": city,
                    "state": state,
                    "country": country,
                    "phone_number": phone,
                    "email_address": email,
                    "social_profiles": {},
                    "source": "web_search",
                    "raw_data": {"snippet": snippet_el.get_text(strip=True) if snippet_el else None},
                }
            )

        return leads

    @staticmethod
    def _resolve_ddg_url(href: str) -> str | None:
        if href.startswith("//duckduckgo.com/l/?"):
            href = "https:" + href
        if "uddg=" in href:
            parsed = urlparse(href)
            params = parse_qs(parsed.query)
            uddg = params.get("uddg", [None])[0]
            if uddg:
                return unquote(uddg)
        if href.startswith("http"):
            return href
        return None
