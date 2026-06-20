"""Advanced audit orchestrator — full multi-category website audit."""

from __future__ import annotations

from typing import Any

import structlog

from app.services.accessibility_service import AccessibilityAnalyzer
from app.services.audit.category_analyzers import (
    AccessibilityCategoryAnalyzer,
    CROAnalyzer,
    FunctionalAnalyzer,
    MarketingAnalyzer,
    MobileAnalyzer,
    QAAnalyzer,
    SEOStrategyAnalyzer,
    SecurityAnalyzer,
    TechnicalSEOAnalyzer,
    TechnologyAnalyzer,
)
from app.services.audit.category_helpers import build_category
from app.services.performance_service import PerformanceAnalyzer
from app.services.scraper.html_parser import HtmlParser
from app.services.scraper.page_fetcher import FetchResult, PageFetcher
from app.services.seo_service import SEOAnalyzer
from app.services.technical_service import TechnicalAnalyzer

logger = structlog.get_logger(__name__)


def _avg(*values: float | None) -> float | None:
    nums = [v for v in values if v is not None]
    return round(sum(nums) / len(nums), 1) if nums else None


def _classify_opportunity(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "hot"
    if score >= 55:
        return "warm"
    if score >= 35:
        return "cold"
    return "low"


class AdvancedAuditEngine:
    """Run a professional-grade website audit across all categories."""

    def __init__(self) -> None:
        self.fetcher = PageFetcher()
        self.seo = SEOAnalyzer(self.fetcher)
        self.performance = PerformanceAnalyzer(self.fetcher)
        self.technical = TechnicalAnalyzer(self.fetcher)
        self.accessibility = AccessibilityAnalyzer()
        self.functional = FunctionalAnalyzer()
        self.mobile = MobileAnalyzer()
        self.security = SecurityAnalyzer()
        self.technical_seo = TechnicalSEOAnalyzer()
        self.seo_strategy = SEOStrategyAnalyzer()
        self.marketing = MarketingAnalyzer()
        self.cro = CROAnalyzer()
        self.qa = QAAnalyzer()
        self.a11y_category = AccessibilityCategoryAnalyzer()
        self.technology = TechnologyAnalyzer()

    def run(
        self,
        url: str,
        *,
        company_name: str | None = None,
        domain: str | None = None,
    ) -> dict[str, Any]:
        logger.info("advanced_audit_start", url=url, company=company_name, domain=domain)

        page = self.fetcher.fetch(url)
        parser = HtmlParser(page.html, page.final_url) if page.html else None
        lighthouse_a11y = self.performance.fetch_lighthouse_accessibility(url)

        seo_data = self.seo.analyze(url, page=page)
        perf_data = self.performance.analyze(url, page=page)
        tech_data = self.technical.analyze(
            url, page=page, lighthouse_accessibility_score=lighthouse_a11y
        )

        a11y_data = (
            self.accessibility.analyze(page, lighthouse_score=lighthouse_a11y)
            if page.html
            else self.accessibility._failed_result(page, lighthouse_a11y)
        )

        categories: dict[str, dict[str, Any]] = {}
        if parser is not None:
            categories["functional"] = self.functional.analyze(page, parser)
            categories["mobile"] = self.mobile.analyze(page, parser)
            categories["technical_seo"] = self.technical_seo.analyze(
                page, parser, seo_data=seo_data, tech_data=tech_data
            )
            categories["seo_strategy"] = self.seo_strategy.analyze(parser, domain=domain)
            categories["marketing"] = self.marketing.analyze(page, parser)
            categories["conversion"] = self.cro.analyze(page, parser)
            categories["qa"] = self.qa.analyze(page, parser)
        else:
            empty = build_category(score=0, issues=[], recommendations=[])
            for key in (
                "functional",
                "mobile",
                "technical_seo",
                "seo_strategy",
                "marketing",
                "conversion",
                "qa",
            ):
                categories[key] = empty

        categories["security"] = self.security.analyze(page, tech_data=tech_data)
        categories["accessibility"] = self.a11y_category.from_a11y_data(a11y_data)
        categories["technology"] = self.technology.analyze(tech_data)
        categories["performance"] = build_category(
            score=perf_data.get("score"),
            issues=(perf_data.get("issues") or {}).get("items", []),
            recommendations=(perf_data.get("recommendations") or {}).get("items", []),
            checks=perf_data.get("metrics") or {},
        )

        seo_score = seo_data.get("score")
        perf_score = perf_data.get("score")
        tech_score = tech_data.get("score")
        security_score = categories["security"].get("score")
        mobile_score = categories["mobile"].get("score")
        technical_seo_score = categories["technical_seo"].get("score")
        accessibility_score = categories["accessibility"].get("score")
        conversion_score = categories["conversion"].get("score")
        marketing_score = categories["marketing"].get("score")
        functional_score = categories["functional"].get("score")
        qa_score = categories["qa"].get("score")

        overall = _avg(
            seo_score,
            perf_score,
            tech_score,
            security_score,
            mobile_score,
            accessibility_score,
        )

        opportunity_signals: list[str] = []
        if (seo_score or 100) < 60:
            opportunity_signals.append("seo_improvement")
        if (perf_score or 100) < 60:
            opportunity_signals.append("performance_improvement")
        if not tech_data.get("ssl_valid"):
            opportunity_signals.append("ssl_missing")
        if (mobile_score or 100) < 60:
            opportunity_signals.append("mobile_unfriendly")
        if (conversion_score or 100) < 60:
            opportunity_signals.append("cro_improvement")
        if (marketing_score or 100) < 60:
            opportunity_signals.append("marketing_gaps")

        lead_opportunity_score = _avg(
            100 - (seo_score or 50),
            100 - (perf_score or 50),
            100 - (tech_score or 50),
            100 - (conversion_score or 50),
        )
        lead_classification = _classify_opportunity(lead_opportunity_score)

        name = company_name or domain or url
        sales_summary = (
            f"{name} scored {overall or 'N/A'}/100 overall. "
            f"Classification: {lead_classification}. "
            f"Categories: SEO {seo_score or '—'}, Performance {perf_score or '—'}, "
            f"Security {security_score or '—'}, Mobile {mobile_score or '—'}, "
            f"CRO {conversion_score or '—'}. "
            f"Opportunities: {', '.join(opportunity_signals) or 'none detected'}."
        )

        category_breakdown = {
            "security": categories["security"],
            "mobile": categories["mobile"],
            "technical_seo": categories["technical_seo"],
            "accessibility": categories["accessibility"],
            "marketing": categories["marketing"],
            "conversion": categories["conversion"],
            "technology": categories["technology"],
            "performance": categories["performance"],
            "functional": categories["functional"],
            "seo_strategy": categories["seo_strategy"],
            "qa": categories["qa"],
        }

        logger.info(
            "advanced_audit_complete",
            url=url,
            overall_score=overall,
            lead_classification=lead_classification,
            category_scores={
                k: v.get("score") for k, v in category_breakdown.items()
            },
        )

        return {
            "seo_data": seo_data,
            "perf_data": perf_data,
            "tech_data": tech_data,
            "a11y_data": a11y_data,
            "qa_data": categories["qa"],
            "functional_data": categories["functional"],
            "scores": {
                "overall": overall,
                "security": security_score,
                "mobile": mobile_score,
                "technical_seo": technical_seo_score,
                "accessibility": accessibility_score,
                "conversion": conversion_score,
                "marketing": marketing_score,
                "functional": functional_score,
                "qa": qa_score,
            },
            "lead_opportunity_score": lead_opportunity_score,
            "lead_classification": lead_classification,
            "sales_summary": sales_summary,
            "category_breakdown": category_breakdown,
            "opportunity_signals": opportunity_signals,
        }
