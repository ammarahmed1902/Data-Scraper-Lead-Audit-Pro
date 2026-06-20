"""Lead scoring engine — composite scores and classification."""

from __future__ import annotations

from typing import Any

import structlog

from app.models.audit import AuditReport, AuditStatus
from app.models.enrichment import BusinessEnrichment, EnrichmentStatus
from app.models.lead_discovery import DiscoveredLead
from app.models.lead_scoring import LeadClassification
from app.services.scoring.opportunity_detector import OpportunityDetector
from app.services.scraper.page_fetcher import PageFetcher

logger = structlog.get_logger(__name__)


class LeadScoringEngine:
    """Calculate lead scores from discovery, enrichment, and audit data."""

    def __init__(self) -> None:
        self.detector = OpportunityDetector()
        self.fetcher = PageFetcher(timeout=15.0, max_retries=1)

    def score(
        self,
        lead: DiscoveredLead,
        audit: AuditReport | None = None,
        enrichment: BusinessEnrichment | None = None,
    ) -> dict[str, Any]:
        html: str | None = None
        if lead.website_url:
            page = self.fetcher.fetch(lead.website_url)
            if page.html and not page.error:
                html = page.html

        website_quality = self._website_quality_score(audit)
        seo_opportunity = self._seo_opportunity_score(audit)
        technical_opportunity = self._technical_opportunity_score(audit)
        sales_potential = self._sales_potential_score(lead, enrichment)

        opportunities = self.detector.detect(lead, audit, enrichment, html)

        # Composite: weighted blend of opportunity + sales potential
        opportunity_avg = (seo_opportunity + technical_opportunity) / 2
        quality_gap = 100 - website_quality if website_quality is not None else 50
        composite = round(
            opportunity_avg * 0.45 + quality_gap * 0.25 + sales_potential * 0.30,
            1,
        )

        classification = self._classify(
            composite=composite,
            sales_potential=sales_potential,
            opportunities=opportunities["items"],
            has_audit=audit is not None and audit.status == AuditStatus.COMPLETED.value,
        )

        return {
            "website_quality_score": website_quality,
            "seo_opportunity_score": seo_opportunity,
            "technical_opportunity_score": technical_opportunity,
            "sales_potential_score": sales_potential,
            "composite_score": composite,
            "classification": classification,
            "opportunities": opportunities["items"],
            "opportunity_summary": opportunities["summary"],
            "audit_id": str(audit.id) if audit else None,
        }

    @staticmethod
    def _website_quality_score(audit: AuditReport | None) -> float | None:
        if audit is None or audit.overall_score is None:
            return None
        return round(float(audit.overall_score), 1)

    @staticmethod
    def _seo_opportunity_score(audit: AuditReport | None) -> float:
        if audit is None or audit.seo_report is None:
            return 40.0  # unaudited baseline opportunity
        seo = audit.seo_report
        if seo.score is None:
            return 50.0
        base = max(0.0, 100.0 - float(seo.score))
        bonus = 0.0
        issues = (seo.issues or {}).get("items", [])
        high_count = sum(1 for i in issues if i.get("severity") in ("critical", "high"))
        bonus = min(25.0, high_count * 5)
        return round(min(100.0, base + bonus), 1)

    @staticmethod
    def _technical_opportunity_score(audit: AuditReport | None) -> float:
        if audit is None or audit.technical_report is None:
            return 40.0
        tech = audit.technical_report
        if tech.score is None:
            return 50.0
        base = max(0.0, 100.0 - float(tech.score))
        issues = (tech.issues or {}).get("items", [])
        critical = sum(1 for i in issues if i.get("severity") == "critical")
        bonus = min(20.0, critical * 8)
        return round(min(100.0, base + bonus), 1)

    @staticmethod
    def _sales_potential_score(
        lead: DiscoveredLead,
        enrichment: BusinessEnrichment | None,
    ) -> float:
        score = 20.0
        if lead.website_url:
            score += 15
        if lead.phone_number:
            score += 20
        if lead.email_address:
            score += 20
        if lead.business_name:
            score += 5
        if lead.city and lead.country:
            score += 5

        if enrichment and enrichment.status == EnrichmentStatus.COMPLETED.value:
            score += 10
            if enrichment.email_addresses:
                score += min(10, len(enrichment.email_addresses) * 5)
            if enrichment.phone_numbers:
                score += min(10, len(enrichment.phone_numbers) * 5)
            if enrichment.services:
                score += 5
            if enrichment.team_members and len(enrichment.team_members) >= 3:
                score += 5

        if lead.imported_website_id:
            score += 5

        return round(min(100.0, score), 1)

    @staticmethod
    def _classify(
        *,
        composite: float,
        sales_potential: float,
        opportunities: list[dict[str, Any]],
        has_audit: bool,
    ) -> str:
        high_opps = sum(1 for o in opportunities if o.get("severity") == "high")

        if composite >= 65 and sales_potential >= 45 and (has_audit or high_opps >= 2):
            return LeadClassification.HOT.value
        if composite >= 40 or (sales_potential >= 55 and high_opps >= 1):
            return LeadClassification.WARM.value
        return LeadClassification.COLD.value
