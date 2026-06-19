"""HTTP page fetcher with retries and timing metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import structlog

logger = structlog.get_logger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; LeadAuditPro/1.0; +https://leadaudit.pro/bot)"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    html: str
    headers: dict[str, str]
    elapsed_ms: float
    content_length: int
    error: str | None = None
    redirects: list[str] = field(default_factory=list)


class PageFetcher:
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        follow_redirects: bool = True,
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.follow_redirects = follow_redirects

    def fetch(self, url: str) -> FetchResult:
        last_error: str | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._fetch_once(url)
            except httpx.HTTPError as exc:
                last_error = str(exc)
                logger.warning(
                    "page_fetch_retry",
                    url=url,
                    attempt=attempt,
                    error=last_error,
                )
                if attempt < self.max_retries:
                    time.sleep(0.5 * attempt)
        return FetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            headers={},
            elapsed_ms=0,
            content_length=0,
            error=last_error or "Failed to fetch page",
        )

    def _fetch_once(self, url: str) -> FetchResult:
        redirects: list[str] = []
        start = time.perf_counter()
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=self.follow_redirects,
            headers=DEFAULT_HEADERS,
        ) as client:
            response = client.get(url)
            if response.history:
                redirects = [str(r.url) for r in response.history]
            elapsed_ms = (time.perf_counter() - start) * 1000
            content = response.text
            return FetchResult(
                url=url,
                final_url=str(response.url),
                status_code=response.status_code,
                html=content,
                headers={k.lower(): v for k, v in response.headers.items()},
                elapsed_ms=elapsed_ms,
                content_length=len(response.content),
                redirects=redirects,
            )

    def head(self, url: str) -> tuple[int, dict[str, str], float]:
        start = time.perf_counter()
        with httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers=DEFAULT_HEADERS,
        ) as client:
            response = client.head(url)
            elapsed_ms = (time.perf_counter() - start) * 1000
            return (
                response.status_code,
                {k.lower(): v for k, v in response.headers.items()},
                elapsed_ms,
            )

    def check_url(self, url: str, base_url: str) -> dict[str, Any]:
        absolute = urljoin(base_url, url)
        parsed = urlparse(absolute)
        if parsed.scheme not in ("http", "https"):
            return {"url": absolute, "status": None, "broken": False, "skipped": True}
        try:
            status, _, _ = self.head(absolute)
            return {
                "url": absolute,
                "status": status,
                "broken": status >= 400,
                "skipped": False,
            }
        except httpx.HTTPError:
            return {"url": absolute, "status": 0, "broken": True, "skipped": False}
