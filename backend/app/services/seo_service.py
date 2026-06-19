"""SEO analysis service — meta tags, headings, links, structured data."""

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import structlog

from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult, PageFetcher

logger = structlog.get_logger(__name__)

MAX_BROKEN_LINK_CHECKS = 15


class SEOAnalyzer:
    def __init__(self, fetcher: PageFetcher | None = None):
        self.fetcher = fetcher or PageFetcher()

    def analyze(self, url: str, page: FetchResult | None = None) -> dict[str, Any]:
        page = page or self.fetcher.fetch(url)
        if page.error or not page.html:
            return self._failed_result(page)

        parser = HtmlParser(page.html, page.final_url)
        title = parser.get_title()
        meta_description = parser.get_meta_description()
        h1_tags = parser.get_headings(1)
        h2_tags = parser.get_headings(2)
        h3_tags = parser.get_headings(3)
        canonical = parser.get_canonical()
        open_graph = parser.get_open_graph()
        structured_data = parser.get_structured_data()
        alt_analysis = parser.get_images_alt_analysis()
        links = parser.get_links()
        internal_links = [l for l in links if l["type"] == "internal"]
        external_links = [l for l in links if l["type"] == "external"]

        has_sitemap = self._check_resource(urljoin(page.final_url, "/sitemap.xml"))
        has_robots_txt = self._check_resource(urljoin(page.final_url, "/robots.txt"))
        broken_links = self._check_broken_links(internal_links[:MAX_BROKEN_LINK_CHECKS], page.final_url)

        issues, recommendations = self._build_issues_and_recommendations(
            title=title,
            meta_description=meta_description,
            h1_tags=h1_tags,
            h2_tags=h2_tags,
            alt_analysis=alt_analysis,
            has_sitemap=has_sitemap,
            has_robots_txt=has_robots_txt,
            canonical=canonical,
            open_graph=open_graph,
            structured_data=structured_data,
            broken_links=broken_links,
            mobile_friendly=parser.is_mobile_friendly(),
        )

        score = self._calculate_score(issues)

        return {
            "score": score,
            "title_tag": title,
            "meta_description": meta_description,
            "h1_count": len(h1_tags),
            "internal_links": len(internal_links),
            "external_links": len(external_links),
            "broken_links": len(broken_links),
            "has_sitemap": has_sitemap,
            "has_robots_txt": has_robots_txt,
            "mobile_friendly": parser.is_mobile_friendly(),
            "issues": {
                "items": issues,
                "meta": {
                    "h1_tags": h1_tags[:10],
                    "h2_tags": h2_tags[:15],
                    "h3_tags": h3_tags[:15],
                    "canonical_url": canonical,
                    "open_graph": open_graph,
                    "structured_data_count": len(structured_data),
                    "structured_data": structured_data[:5],
                    "alt_tags": alt_analysis,
                    "broken_link_details": broken_links,
                },
            },
            "recommendations": {"items": recommendations},
        }

    def _check_resource(self, url: str) -> bool:
        try:
            status, _, _ = self.fetcher.head(url)
            return status < 400
        except Exception:
            return False

    def _check_broken_links(self, links: list[dict[str, str]], base_url: str) -> list[dict[str, Any]]:
        broken: list[dict[str, Any]] = []
        for link in links:
            result = self.fetcher.check_url(link["url"], base_url)
            if result.get("broken"):
                broken.append(result)
        return broken

    def _build_issues_and_recommendations(
        self,
        *,
        title: str | None,
        meta_description: str | None,
        h1_tags: list[str],
        h2_tags: list[str],
        alt_analysis: dict[str, Any],
        has_sitemap: bool,
        has_robots_txt: bool,
        canonical: str | None,
        open_graph: dict[str, str],
        structured_data: list[dict[str, Any]],
        broken_links: list[dict[str, Any]],
        mobile_friendly: bool,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        if not title:
            issues.append({"severity": "critical", "code": "MISSING_TITLE", "message": "Page is missing a title tag"})
            recommendations.append({"priority": "high", "title": "Add a title tag", "description": "Include a unique, descriptive title between 30-60 characters."})
        elif len(title) < 30:
            issues.append({"severity": "medium", "code": "SHORT_TITLE", "message": f"Title is too short ({len(title)} chars)"})
            recommendations.append({"priority": "medium", "title": "Expand title tag", "description": "Aim for 30-60 characters with primary keywords."})
        elif len(title) > 60:
            issues.append({"severity": "low", "code": "LONG_TITLE", "message": f"Title may be truncated ({len(title)} chars)"})

        if not meta_description:
            issues.append({"severity": "high", "code": "MISSING_META_DESCRIPTION", "message": "Missing meta description"})
            recommendations.append({"priority": "high", "title": "Add meta description", "description": "Write a compelling 120-160 character meta description."})
        elif len(meta_description) < 70:
            issues.append({"severity": "medium", "code": "SHORT_META_DESCRIPTION", "message": "Meta description is too short"})
        elif len(meta_description) > 160:
            issues.append({"severity": "low", "code": "LONG_META_DESCRIPTION", "message": "Meta description may be truncated in SERPs"})

        if len(h1_tags) == 0:
            issues.append({"severity": "high", "code": "MISSING_H1", "message": "No H1 heading found"})
            recommendations.append({"priority": "high", "title": "Add an H1 heading", "description": "Use exactly one H1 that describes the page topic."})
        elif len(h1_tags) > 1:
            issues.append({"severity": "medium", "code": "MULTIPLE_H1", "message": f"Found {len(h1_tags)} H1 tags"})
            recommendations.append({"priority": "medium", "title": "Use a single H1", "description": "Consolidate to one primary H1 per page."})

        if not h2_tags:
            issues.append({"severity": "low", "code": "MISSING_H2", "message": "No H2 subheadings found"})
            recommendations.append({"priority": "low", "title": "Add H2 subheadings", "description": "Structure content with descriptive H2 sections."})

        total_images = alt_analysis.get("total_images", 0)
        missing_alt = alt_analysis.get("missing_alt", 0) + alt_analysis.get("empty_alt", 0)
        if total_images > 0 and missing_alt / total_images > 0.2:
            issues.append({"severity": "medium", "code": "MISSING_ALT_TAGS", "message": f"{missing_alt}/{total_images} images lack alt text"})
            recommendations.append({"priority": "medium", "title": "Add image alt text", "description": "Provide descriptive alt attributes for accessibility and SEO."})

        if not has_sitemap:
            issues.append({"severity": "medium", "code": "MISSING_SITEMAP", "message": "No sitemap.xml detected"})
            recommendations.append({"priority": "medium", "title": "Create XML sitemap", "description": "Submit sitemap.xml to help search engines discover pages."})

        if not has_robots_txt:
            issues.append({"severity": "low", "code": "MISSING_ROBOTS_TXT", "message": "No robots.txt found"})
            recommendations.append({"priority": "low", "title": "Add robots.txt", "description": "Configure crawl directives via robots.txt."})

        if not canonical:
            issues.append({"severity": "medium", "code": "MISSING_CANONICAL", "message": "No canonical tag found"})
            recommendations.append({"priority": "medium", "title": "Add canonical URL", "description": "Specify the preferred URL to avoid duplicate content issues."})

        if not open_graph.get("og:title"):
            issues.append({"severity": "low", "code": "MISSING_OPEN_GRAPH", "message": "Open Graph tags are incomplete"})
            recommendations.append({"priority": "low", "title": "Add Open Graph tags", "description": "Improve social sharing with og:title, og:description, and og:image."})

        if not structured_data:
            issues.append({"severity": "low", "code": "MISSING_STRUCTURED_DATA", "message": "No JSON-LD structured data found"})
            recommendations.append({"priority": "low", "title": "Add structured data", "description": "Use Schema.org JSON-LD for rich search results."})

        if broken_links:
            issues.append({"severity": "high", "code": "BROKEN_LINKS", "message": f"Found {len(broken_links)} broken internal links"})
            recommendations.append({"priority": "high", "title": "Fix broken links", "description": "Repair or remove broken internal links."})

        if not mobile_friendly:
            issues.append({"severity": "high", "code": "NOT_MOBILE_FRIENDLY", "message": "Missing mobile viewport meta tag"})
            recommendations.append({"priority": "high", "title": "Enable mobile viewport", "description": "Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">."})

        return issues, recommendations

    def _calculate_score(self, issues: list[dict[str, Any]]) -> float:
        score = 100.0
        weights = {"critical": 20, "high": 12, "medium": 7, "low": 3}
        for issue in issues:
            score -= weights.get(issue.get("severity", "low"), 3)
        return max(0.0, min(100.0, round(score, 1)))

    def _failed_result(self, page: FetchResult) -> dict[str, Any]:
        message = page.error or f"HTTP {page.status_code}"
        return {
            "score": 0.0,
            "title_tag": None,
            "meta_description": None,
            "h1_count": 0,
            "internal_links": 0,
            "external_links": 0,
            "broken_links": 0,
            "has_sitemap": False,
            "has_robots_txt": False,
            "mobile_friendly": False,
            "issues": {"items": [{"severity": "critical", "code": "FETCH_FAILED", "message": message}], "meta": {}},
            "recommendations": {"items": [{"priority": "high", "title": "Fix page accessibility", "description": "Ensure the URL is reachable and returns valid HTML."}]},
        }


class SEOService:
    """Async-compatible wrapper used by audit runner."""

    def analyze(self, url: str, page: FetchResult | None = None) -> dict[str, Any]:
        return SEOAnalyzer().analyze(url, page)
