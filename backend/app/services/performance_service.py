"""Performance analysis service — PageSpeed API and HTTP timing fallback."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.core.config import settings
from app.services.scraper.page_fetcher import FetchResult, PageFetcher

logger = structlog.get_logger(__name__)

PAGESPEED_API = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PerformanceAnalyzer:
    def __init__(self, fetcher: PageFetcher | None = None):
        self.fetcher = fetcher or PageFetcher()

    def analyze(self, url: str, page: FetchResult | None = None) -> dict[str, Any]:
        if settings.PAGESPEED_API_KEY:
            pagespeed = self._analyze_pagespeed(url)
            if pagespeed:
                return pagespeed
        return self._analyze_fallback(url, page)

    def fetch_lighthouse_accessibility(self, url: str) -> float | None:
        """Fetch Lighthouse accessibility score (0-100) when API key is configured."""
        if not settings.PAGESPEED_API_KEY:
            return None
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(
                    PAGESPEED_API,
                    params={
                        "url": url,
                        "key": settings.PAGESPEED_API_KEY,
                        "strategy": "mobile",
                        "category": "accessibility",
                    },
                )
                if response.status_code != 200:
                    return None
                data = response.json()
                score = data.get("lighthouseResult", {}).get("categories", {}).get(
                    "accessibility", {}
                ).get("score")
                return round((score or 0) * 100, 1) if score is not None else None
        except Exception as exc:
            logger.warning("pagespeed_accessibility_failed", error=str(exc))
            return None

    def _analyze_pagespeed(self, url: str) -> dict[str, Any] | None:
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.get(
                    PAGESPEED_API,
                    params={
                        "url": url,
                        "key": settings.PAGESPEED_API_KEY,
                        "strategy": "mobile",
                        "category": "performance",
                    },
                )
                if response.status_code != 200:
                    logger.warning("pagespeed_api_error", status=response.status_code)
                    return None
                data = response.json()
                lighthouse = data.get("lighthouseResult", {})
                audits = lighthouse.get("audits", {})
                categories = lighthouse.get("categories", {})
                perf_score = categories.get("performance", {}).get("score")
                score = round((perf_score or 0) * 100, 1)

                def metric_value(audit_id: str) -> float | None:
                    audit = audits.get(audit_id, {})
                    val = audit.get("numericValue")
                    return round(val, 2) if val is not None else None

                fcp = metric_value("first-contentful-paint")
                lcp = metric_value("largest-contentful-paint")
                cls = metric_value("cumulative-layout-shift")
                ttfb = metric_value("server-response-time")
                speed_index = metric_value("speed-index")
                tbt = metric_value("total-blocking-time")

                issues, recommendations = self._build_issues(
                    score=score,
                    lcp=lcp,
                    cls=cls,
                    fcp=fcp,
                    ttfb=ttfb,
                )

                return {
                    "score": score,
                    "load_time_ms": ttfb,
                    "first_contentful_paint": fcp,
                    "largest_contentful_paint": lcp,
                    "time_to_interactive": metric_value("interactive"),
                    "total_blocking_time": tbt,
                    "cumulative_layout_shift": cls,
                    "page_size_kb": None,
                    "request_count": None,
                    "metrics": {
                        "source": "pagespeed",
                        "speed_index": speed_index,
                        "ttfb": ttfb,
                        "fcp": fcp,
                        "lcp": lcp,
                        "cls": cls,
                        "performance_score": score,
                    },
                    "recommendations": {"items": recommendations},
                    "issues": {"items": issues, "meta": {"source": "pagespeed"}},
                }
        except Exception as exc:
            logger.warning("pagespeed_fetch_failed", error=str(exc))
            return None

    def _analyze_fallback(self, url: str, page: FetchResult | None = None) -> dict[str, Any]:
        page = page or self.fetcher.fetch(url)
        elapsed = page.elapsed_ms
        page_size_kb = round(page.content_length / 1024, 2) if page.content_length else 0

        estimated_fcp = round(elapsed * 0.4, 2)
        estimated_lcp = round(elapsed * 0.75, 2)
        estimated_ttfb = round(elapsed * 0.15, 2)

        score = 100.0
        if elapsed > 3000:
            score -= 40
        elif elapsed > 1500:
            score -= 20
        elif elapsed > 800:
            score -= 10

        if page_size_kb > 3000:
            score -= 20
        elif page_size_kb > 1500:
            score -= 10

        if page.error or page.status_code >= 400:
            score = 0

        score = max(0.0, min(100.0, round(score, 1)))
        issues, recommendations = self._build_issues(
            score=score,
            lcp=estimated_lcp,
            cls=None,
            fcp=estimated_fcp,
            ttfb=estimated_ttfb,
            load_time_ms=elapsed,
            page_size_kb=page_size_kb,
        )

        return {
            "score": score,
            "load_time_ms": elapsed,
            "first_contentful_paint": estimated_fcp,
            "largest_contentful_paint": estimated_lcp,
            "time_to_interactive": round(elapsed * 0.9, 2),
            "total_blocking_time": None,
            "cumulative_layout_shift": None,
            "page_size_kb": page_size_kb,
            "request_count": 1,
            "metrics": {
                "source": "http_fallback",
                "ttfb": estimated_ttfb,
                "fcp": estimated_fcp,
                "lcp": estimated_lcp,
                "load_time_ms": elapsed,
                "page_size_kb": page_size_kb,
            },
            "recommendations": {"items": recommendations},
            "issues": {"items": issues, "meta": {"source": "http_fallback"}},
        }

    def _build_issues(
        self,
        *,
        score: float,
        lcp: float | None,
        cls: float | None,
        fcp: float | None,
        ttfb: float | None,
        load_time_ms: float | None = None,
        page_size_kb: float | None = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        if lcp is not None and lcp > 2500:
            issues.append({"severity": "high", "code": "POOR_LCP", "message": f"LCP is {lcp}ms (target < 2500ms)"})
            recommendations.append({"priority": "high", "title": "Improve Largest Contentful Paint", "description": "Optimize hero images, fonts, and server response time."})

        if cls is not None and cls > 0.1:
            issues.append({"severity": "medium", "code": "POOR_CLS", "message": f"CLS is {cls} (target < 0.1)"})
            recommendations.append({"priority": "medium", "title": "Reduce layout shift", "description": "Set explicit dimensions on images and embeds."})

        if fcp is not None and fcp > 1800:
            issues.append({"severity": "medium", "code": "POOR_FCP", "message": f"FCP is {fcp}ms (target < 1800ms)"})
            recommendations.append({"priority": "medium", "title": "Improve First Contentful Paint", "description": "Reduce render-blocking resources and optimize CSS."})

        if ttfb is not None and ttfb > 600:
            issues.append({"severity": "medium", "code": "POOR_TTFB", "message": f"TTFB is {ttfb}ms (target < 600ms)"})
            recommendations.append({"priority": "medium", "title": "Reduce server response time", "description": "Use CDN, caching, and optimize backend performance."})

        if load_time_ms and load_time_ms > 3000:
            issues.append({"severity": "high", "code": "SLOW_LOAD", "message": f"Page load time is {load_time_ms:.0f}ms"})
            recommendations.append({"priority": "high", "title": "Reduce page load time", "description": "Compress assets, enable caching, and minimize JavaScript."})

        if page_size_kb and page_size_kb > 2000:
            issues.append({"severity": "medium", "code": "LARGE_PAGE", "message": f"Page size is {page_size_kb}KB"})
            recommendations.append({"priority": "medium", "title": "Reduce page weight", "description": "Compress images and remove unused resources."})

        if score < 50:
            issues.append({"severity": "critical", "code": "LOW_PERFORMANCE_SCORE", "message": f"Performance score is {score}"})
        elif score < 75:
            issues.append({"severity": "medium", "code": "MODERATE_PERFORMANCE", "message": f"Performance score is {score} — room for improvement"})

        return issues, recommendations


class PerformanceService:
    def analyze(self, url: str, page: FetchResult | None = None) -> dict[str, Any]:
        return PerformanceAnalyzer().analyze(url, page)

    def fetch_lighthouse_accessibility(self, url: str) -> float | None:
        return PerformanceAnalyzer().fetch_lighthouse_accessibility(url)
