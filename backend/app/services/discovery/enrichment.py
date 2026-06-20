"""Enrich discovered leads with email and social profiles from public websites."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import structlog
from bs4 import BeautifulSoup

logger = structlog.get_logger(__name__)

EMAIL_PATTERN = re.compile(
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

SOCIAL_DOMAINS = {
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "youtube.com": "youtube",
    "tiktok.com": "tiktok",
    "yelp.com": "yelp",
}


class LeadEnrichmentService:
    def __init__(self, user_agent: str, request_delay_seconds: float = 1.0):
        self.user_agent = user_agent
        self.request_delay_seconds = request_delay_seconds
        self._last_request_at = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def enrich(self, lead: dict[str, Any]) -> dict[str, Any]:
        url = lead.get("website_url")
        if not url:
            return lead

        try:
            self._rate_limit()
            with httpx.Client(
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": self.user_agent},
            ) as client:
                response = client.get(url)
                if response.status_code >= 400:
                    return lead
                html = response.text
        except Exception as exc:
            logger.debug("lead_enrichment_fetch_failed", url=url, error=str(exc))
            return lead

        soup = BeautifulSoup(html, "lxml")
        if not lead.get("email_address"):
            lead["email_address"] = self._extract_email(soup, html)

        social = lead.get("social_profiles") or {}
        social.update(self._extract_social_profiles(soup, url))
        if social:
            lead["social_profiles"] = social

        return lead

    def _extract_email(self, soup: BeautifulSoup, html: str) -> str | None:
        for anchor in soup.select('a[href^="mailto:"]'):
            href = anchor.get("href", "")
            email = href.replace("mailto:", "").split("?")[0].strip()
            if EMAIL_PATTERN.fullmatch(email):
                return email.lower()
        for match in EMAIL_PATTERN.findall(html):
            lowered = match.lower()
            if not any(
                skip in lowered
                for skip in ("example.com", "wixpress.com", "sentry.io", "schema.org")
            ):
                return lowered
        return None

    def _extract_social_profiles(
        self, soup: BeautifulSoup, base_url: str
    ) -> dict[str, str]:
        profiles: dict[str, str] = {}
        for anchor in soup.find_all("a", href=True):
            href = urljoin(base_url, anchor["href"])
            parsed = urlparse(href)
            host = parsed.netloc.lower().removeprefix("www.")
            for domain, platform in SOCIAL_DOMAINS.items():
                if domain in host and platform not in profiles:
                    profiles[platform] = href
        return profiles
