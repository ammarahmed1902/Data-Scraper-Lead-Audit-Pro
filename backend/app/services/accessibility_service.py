"""Accessibility analysis — HTML heuristics and Lighthouse integration."""

from __future__ import annotations

from typing import Any

from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult


class AccessibilityAnalyzer:
    """Analyze page accessibility using static HTML signals."""

    def analyze(
        self,
        page: FetchResult,
        lighthouse_score: float | None = None,
    ) -> dict[str, Any]:
        if page.error or not page.html:
            return self._failed_result(page, lighthouse_score)

        parser = HtmlParser(page.html, page.final_url)
        soup = parser.soup
        issues: list[dict[str, Any]] = []
        recommendations: list[dict[str, Any]] = []

        html_tag = soup.find("html")
        lang = html_tag.get("lang") if html_tag else None
        if not lang:
            issues.append({
                "severity": "medium",
                "code": "MISSING_LANG",
                "message": "HTML element missing lang attribute",
            })
            recommendations.append({
                "priority": "medium",
                "title": "Add lang attribute",
                "description": 'Set <html lang="en"> (or appropriate language code).',
            })

        if not parser.get_title():
            issues.append({
                "severity": "high",
                "code": "MISSING_PAGE_TITLE",
                "message": "Page has no title for screen readers",
            })

        alt_analysis = parser.get_images_alt_analysis()
        missing_alt = alt_analysis.get("missing_alt", 0) + alt_analysis.get("empty_alt", 0)
        total_images = alt_analysis.get("total_images", 0)
        if total_images > 0 and missing_alt > 0:
            issues.append({
                "severity": "high",
                "code": "IMAGES_MISSING_ALT",
                "message": f"{missing_alt}/{total_images} images lack descriptive alt text",
            })
            recommendations.append({
                "priority": "high",
                "title": "Add alt text to images",
                "description": "Every informative image needs descriptive alt text.",
            })

        unlabeled_inputs = 0
        for inp in soup.find_all("input"):
            input_type = (inp.get("type") or "text").lower()
            if input_type in ("hidden", "submit", "button", "image"):
                continue
            inp_id = inp.get("id")
            has_label = bool(inp_id and soup.find("label", attrs={"for": inp_id}))
            has_aria = bool(inp.get("aria-label") or inp.get("aria-labelledby"))
            if not has_label and not has_aria:
                unlabeled_inputs += 1
        if unlabeled_inputs:
            issues.append({
                "severity": "high",
                "code": "UNLABELED_INPUTS",
                "message": f"{unlabeled_inputs} form inputs lack labels",
            })
            recommendations.append({
                "priority": "high",
                "title": "Label form fields",
                "description": "Associate each input with a <label> or aria-label.",
            })

        empty_links = 0
        for anchor in soup.find_all("a"):
            text = anchor.get_text(strip=True)
            aria = anchor.get("aria-label") or anchor.get("title")
            if not text and not aria:
                empty_links += 1
        if empty_links:
            issues.append({
                "severity": "medium",
                "code": "EMPTY_LINKS",
                "message": f"{empty_links} links have no accessible text",
            })

        if not soup.find("main") and not soup.find(attrs={"role": "main"}):
            issues.append({
                "severity": "low",
                "code": "MISSING_MAIN_LANDMARK",
                "message": "No main landmark found",
            })
            recommendations.append({
                "priority": "low",
                "title": "Add main landmark",
                "description": "Use <main> or role=\"main\" for primary content.",
            })

        headings = []
        for level in range(1, 7):
            for _h in soup.find_all(f"h{level}"):
                headings.append(level)
        if headings and headings[0] != 1:
            issues.append({
                "severity": "low",
                "code": "HEADING_HIERARCHY",
                "message": "Page does not start with an H1 heading",
            })

        score = self._calculate_score(issues, lighthouse_score)

        return {
            "score": score,
            "lighthouse_score": lighthouse_score,
            "checks": {
                "lang_attribute": bool(lang),
                "page_title": bool(parser.get_title()),
                "images_with_alt": total_images - missing_alt if total_images else None,
                "total_images": total_images,
                "unlabeled_inputs": unlabeled_inputs,
                "empty_links": empty_links,
                "has_main_landmark": bool(
                    soup.find("main") or soup.find(attrs={"role": "main"})
                ),
            },
            "issues": {"items": issues, "meta": {"alt_analysis": alt_analysis}},
            "recommendations": {"items": recommendations},
        }

    def _calculate_score(
        self, issues: list[dict[str, Any]], lighthouse_score: float | None
    ) -> float:
        if lighthouse_score is not None:
            heuristic = 100.0
            weights = {"critical": 20, "high": 12, "medium": 7, "low": 3}
            for issue in issues:
                heuristic -= weights.get(issue.get("severity", "low"), 3)
            heuristic = max(0.0, min(100.0, round(heuristic, 1)))
            return round((lighthouse_score * 0.7) + (heuristic * 0.3), 1)

        score = 100.0
        weights = {"critical": 20, "high": 12, "medium": 7, "low": 3}
        for issue in issues:
            score -= weights.get(issue.get("severity", "low"), 3)
        return max(0.0, min(100.0, round(score, 1)))

    def _failed_result(
        self, page: FetchResult, lighthouse_score: float | None
    ) -> dict[str, Any]:
        message = page.error or f"HTTP {page.status_code}"
        return {
            "score": 0.0,
            "lighthouse_score": lighthouse_score,
            "checks": {},
            "issues": {
                "items": [{"severity": "critical", "code": "FETCH_FAILED", "message": message}],
                "meta": {},
            },
            "recommendations": {"items": []},
        }
