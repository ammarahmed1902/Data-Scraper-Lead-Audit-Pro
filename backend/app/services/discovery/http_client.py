"""Rate-limited HTTP client for ethical discovery scraping."""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class DiscoveryFetchResult:
    url: str
    final_url: str
    status_code: int
    html: str
    elapsed_ms: float
    error: str | None = None
    retries: int = 0


class DiscoveryHttpClient:
    """Sequential HTTP client with per-request delay, retries, and 429 backoff."""

    def __init__(
        self,
        *,
        user_agent: str,
        request_delay_seconds: float = 1.5,
        max_retries: int = 3,
        backoff_seconds: float = 2.0,
        timeout_seconds: float = 30.0,
    ):
        self.user_agent = user_agent
        self.request_delay_seconds = request_delay_seconds
        self.max_retries = max_retries
        self.backoff_seconds = backoff_seconds
        self.timeout_seconds = timeout_seconds
        self._last_request_at = 0.0

    def _rate_limit(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.request_delay_seconds:
            time.sleep(self.request_delay_seconds - elapsed)
        self._last_request_at = time.monotonic()

    def fetch(self, url: str) -> DiscoveryFetchResult:
        last_error: str | None = None
        retries = 0

        for attempt in range(1, self.max_retries + 1):
            self._rate_limit()
            start = time.perf_counter()
            try:
                with httpx.Client(
                    timeout=self.timeout_seconds,
                    follow_redirects=True,
                    headers={
                        "User-Agent": self.user_agent,
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.9",
                    },
                ) as client:
                    response = client.get(url)
                    elapsed_ms = (time.perf_counter() - start) * 1000

                    if response.status_code == 429:
                        wait = self.backoff_seconds * attempt
                        logger.warning(
                            "discovery_rate_limited",
                            url=url,
                            attempt=attempt,
                            wait_seconds=wait,
                        )
                        time.sleep(wait)
                        retries += 1
                        last_error = "HTTP 429 Too Many Requests"
                        continue

                    if response.status_code >= 500:
                        last_error = f"HTTP {response.status_code}"
                        retries += 1
                        if attempt < self.max_retries:
                            time.sleep(self.backoff_seconds * attempt)
                        continue

                    if response.status_code >= 400:
                        return DiscoveryFetchResult(
                            url=url,
                            final_url=str(response.url),
                            status_code=response.status_code,
                            html="",
                            elapsed_ms=elapsed_ms,
                            error=f"HTTP {response.status_code}",
                            retries=retries,
                        )

                    return DiscoveryFetchResult(
                        url=url,
                        final_url=str(response.url),
                        status_code=response.status_code,
                        html=response.text,
                        elapsed_ms=elapsed_ms,
                        retries=retries,
                    )
            except httpx.HTTPError as exc:
                last_error = str(exc)
                retries += 1
                logger.warning(
                    "discovery_fetch_retry",
                    url=url,
                    attempt=attempt,
                    error=last_error,
                )
                if attempt < self.max_retries:
                    time.sleep(self.backoff_seconds * attempt)

        return DiscoveryFetchResult(
            url=url,
            final_url=url,
            status_code=0,
            html="",
            elapsed_ms=0,
            error=last_error or "Failed to fetch page",
            retries=retries,
        )
