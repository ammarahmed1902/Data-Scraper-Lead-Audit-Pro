"""Detect sales opportunities from audit data and page HTML."""

from __future__ import annotations

import re
from typing import Any

from app.models.audit import AuditReport
from app.models.enrichment import BusinessEnrichment
from app.models.lead_discovery import DiscoveredLead

TRACKING_PATTERNS = {
    "google_analytics": (
        r"google-analytics\.com",
        r"googletagmanager\.com/gtag",
        r"gtag\s*\(",
        r"GA_MEASUREMENT_ID",
        r"G-[A-Z0-9]{6,}",
    ),
    "google_tag_manager": (r"googletagmanager\.com/gtm", r"GTM-[A-Z0-9]+"),
    "facebook_pixel": (r"connect\.facebook\.net", r"fbq\s*\(", r"facebook\.com/tr"),
    "linkedin_insight": (r"snap\.licdn\.com", r"_linkedin_partner_id"),
    "hotjar": (r"hotjar\.com", r"hj\s*\("),
    "hubspot": (r"js\.hs-scripts\.com", r"hubspot"),
}

CONVERSION_PATTERNS = (
    r'type=["\']submit["\']',
    r"<form",
    r'href=["\']tel:',
    r'href=["\']mailto:',
    r'class=["\'][^"\']*(?:cta|btn-primary|call-to-action|contact-btn)',
    r"id=['\"]contact-form",
)


class OpportunityDetector:
    """Identify actionable sales opportunities for a lead."""

    def detect(
        self,
        lead: DiscoveredLead,
        audit: AuditReport | None,
        enrichment: BusinessEnrichment | None,
        html: str | None = None,
    ) -> dict[str, Any]:
        opportunities: list[dict[str, Any]] = []
        html_lower = (html or "").lower()

        self._check_seo(audit, opportunities)
        self._check_performance(audit, opportunities)
        self._check_technical(audit, opportunities)
        self._check_tracking(html_lower, opportunities)
        self._check_analytics(html_lower, audit, opportunities)
        self._check_conversion(html_lower, audit, enrichment, lead, opportunities)

        summary = {
            "total": len(opportunities),
            "high": sum(1 for o in opportunities if o.get("severity") == "high"),
            "medium": sum(1 for o in opportunities if o.get("severity") == "medium"),
            "categories": sorted({o["category"] for o in opportunities}),
        }
        return {"items": opportunities, "summary": summary}

    def _check_seo(self, audit: AuditReport | None, out: list[dict[str, Any]]) -> None:
        if audit is None or audit.seo_report is None:
            out.append({
                "category": "missing_seo",
                "code": "NOT_AUDITED",
                "severity": "medium",
                "title": "No SEO audit data",
                "description": "Run an audit to assess SEO gaps.",
            })
            return

        seo = audit.seo_report
        issue_codes = {
            item.get("code")
            for item in (seo.issues or {}).get("items", [])
            if isinstance(item, dict)
        }
        seo_gaps = {
            "MISSING_TITLE": "Missing meta title",
            "MISSING_META_DESCRIPTION": "Missing meta description",
            "MISSING_H1": "No H1 heading",
            "MISSING_SITEMAP": "No sitemap.xml",
            "MISSING_ROBOTS_TXT": "No robots.txt",
            "MISSING_CANONICAL": "No canonical tag",
            "BROKEN_LINKS": "Broken internal links",
            "NOT_MOBILE_FRIENDLY": "Not mobile-friendly",
        }
        found = False
        for code, title in seo_gaps.items():
            if code in issue_codes:
                found = True
                out.append({
                    "category": "missing_seo",
                    "code": code,
                    "severity": "high" if code in ("MISSING_TITLE", "MISSING_H1", "BROKEN_LINKS") else "medium",
                    "title": title,
                    "description": f"SEO issue detected: {title}",
                })
        if not found and seo.score is not None and seo.score >= 80:
            pass  # good SEO — no missing_seo opportunity

    def _check_performance(self, audit: AuditReport | None, out: list[dict[str, Any]]) -> None:
        if audit is None or audit.performance_report is None:
            return
        perf = audit.performance_report
        if perf.score is not None and perf.score < 50:
            out.append({
                "category": "poor_performance",
                "code": "LOW_PERFORMANCE",
                "severity": "high",
                "title": "Poor performance score",
                "description": f"Performance score is {perf.score}/100",
            })
        if perf.largest_contentful_paint and perf.largest_contentful_paint > 2500:
            out.append({
                "category": "poor_performance",
                "code": "POOR_LCP",
                "severity": "high",
                "title": "Slow Largest Contentful Paint",
                "description": f"LCP is {perf.largest_contentful_paint:.0f}ms (target < 2500ms)",
            })
        issue_codes = {
            item.get("code")
            for item in (perf.issues or {}).get("items", [])
            if isinstance(item, dict)
        }
        for code in ("POOR_FCP", "POOR_CLS", "POOR_TTFB", "SLOW_LOAD"):
            if code in issue_codes:
                out.append({
                    "category": "poor_performance",
                    "code": code,
                    "severity": "medium",
                    "title": code.replace("_", " ").title(),
                    "description": "Core Web Vitals need improvement",
                })

    def _check_technical(self, audit: AuditReport | None, out: list[dict[str, Any]]) -> None:
        if audit is None or audit.technical_report is None:
            return
        tech = audit.technical_report
        issue_codes = {
            item.get("code")
            for item in (tech.issues or {}).get("items", [])
            if isinstance(item, dict)
        }
        critical_codes = {
            "NO_HTTPS": "Site not using HTTPS",
            "INVALID_SSL": "Invalid SSL certificate",
            "HTTP_ERROR": "HTTP errors on page",
            "SSL_EXPIRING": "SSL certificate expiring soon",
        }
        for code, title in critical_codes.items():
            if code in issue_codes:
                out.append({
                    "category": "technical_problems",
                    "code": code,
                    "severity": "high",
                    "title": title,
                    "description": f"Technical issue: {title}",
                })
        if tech.security_headers:
            missing = tech.security_headers.get("missing", [])
            if len(missing) >= 3:
                out.append({
                    "category": "technical_problems",
                    "code": "MISSING_SECURITY_HEADERS",
                    "severity": "medium",
                    "title": "Missing security headers",
                    "description": f"Missing {len(missing)} security headers",
                })

    def _check_tracking(self, html: str, out: list[dict[str, Any]]) -> None:
        if not html:
            return
        has_any = False
        for _name, patterns in TRACKING_PATTERNS.items():
            if any(re.search(p, html, re.I) for p in patterns):
                has_any = True
                break
        if not has_any:
            out.append({
                "category": "missing_tracking_pixels",
                "code": "NO_TRACKING_PIXELS",
                "severity": "medium",
                "title": "No tracking pixels detected",
                "description": "No Facebook Pixel, GTM, or similar tracking found.",
            })

    def _check_analytics(
        self, html: str, audit: AuditReport | None, out: list[dict[str, Any]]
    ) -> None:
        has_ga = html and any(
            re.search(p, html, re.I) for p in TRACKING_PATTERNS["google_analytics"]
        )
        has_gtm = html and any(
            re.search(p, html, re.I) for p in TRACKING_PATTERNS["google_tag_manager"]
        )
        if html and not has_ga and not has_gtm:
            out.append({
                "category": "missing_analytics",
                "code": "NO_ANALYTICS",
                "severity": "high",
                "title": "No analytics installed",
                "description": "Google Analytics or GTM not detected on the website.",
            })
        elif not html and audit is None:
            out.append({
                "category": "missing_analytics",
                "code": "ANALYTICS_UNKNOWN",
                "severity": "low",
                "title": "Analytics status unknown",
                "description": "Audit required to verify analytics installation.",
            })

    def _check_conversion(
        self,
        html: str,
        audit: AuditReport | None,
        enrichment: BusinessEnrichment | None,
        lead: DiscoveredLead,
        out: list[dict[str, Any]],
    ) -> None:
        has_form = html and re.search(CONVERSION_PATTERNS[1], html, re.I)
        has_cta = html and (
            re.search(CONVERSION_PATTERNS[0], html, re.I)
            or re.search(CONVERSION_PATTERNS[4], html, re.I)
            or re.search(CONVERSION_PATTERNS[5], html, re.I)
        )
        has_contact = bool(
            lead.phone_number
            or lead.email_address
            or (enrichment and enrichment.email_addresses)
            or (enrichment and enrichment.phone_numbers)
        )
        if html and not has_form and not has_cta:
            out.append({
                "category": "missing_conversion_elements",
                "code": "NO_CONVERSION_ELEMENTS",
                "severity": "high",
                "title": "Missing conversion elements",
                "description": "No contact forms or clear CTAs detected on homepage.",
            })
        elif not has_contact and not has_form:
            out.append({
                "category": "missing_conversion_elements",
                "code": "NO_CONTACT_PATH",
                "severity": "medium",
                "title": "Limited contact options",
                "description": "No contact form and no phone/email on record.",
            })
