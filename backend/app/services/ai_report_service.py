"""AI-powered full report content generation."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class AIReportService:
    """Generate client-ready audit report content."""

    def generate_full_report(
        self,
        *,
        url: str,
        domain: str,
        company_name: str | None,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
        overall_score: float,
        opportunities: list[dict[str, Any]] | None = None,
        lead_classification: str | None = None,
    ) -> dict[str, Any]:
        if settings.OPENAI_API_KEY:
            ai_content = self._generate_with_openai(
                url=url,
                domain=domain,
                company_name=company_name,
                seo=seo,
                performance=performance,
                technical=technical,
                overall_score=overall_score,
                opportunities=opportunities or [],
                lead_classification=lead_classification,
            )
            if ai_content:
                return ai_content

        return self._generate_template_report(
            url=url,
            domain=domain,
            company_name=company_name,
            seo=seo,
            performance=performance,
            technical=technical,
            overall_score=overall_score,
            opportunities=opportunities or [],
            lead_classification=lead_classification,
        )

    def generate_executive_summary(
        self,
        *,
        url: str,
        domain: str,
        company_name: str | None,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
        overall_score: float,
    ) -> str:
        content = self.generate_full_report(
            url=url,
            domain=domain,
            company_name=company_name,
            seo=seo,
            performance=performance,
            technical=technical,
            overall_score=overall_score,
        )
        return content["executive_summary"]

    def generate_sales_opportunity(
        self,
        *,
        domain: str,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
    ) -> str:
        content = self.generate_full_report(
            url=f"https://{domain}",
            domain=domain,
            company_name=None,
            seo=seo,
            performance=performance,
            technical=technical,
            overall_score=(
                (seo.get("score") or 0) + (performance.get("score") or 0) + (technical.get("score") or 0)
            )
            / 3,
        )
        return content["opportunity_summary"]

    def _generate_template_report(
        self,
        *,
        url: str,
        domain: str,
        company_name: str | None,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
        overall_score: float,
        opportunities: list[dict[str, Any]],
        lead_classification: str | None,
    ) -> dict[str, Any]:
        name = company_name or domain
        seo_score = seo.get("score") or 0
        perf_score = performance.get("score") or 0
        tech_score = technical.get("score") or 0

        grade = (
            "excellent" if overall_score >= 85
            else "good" if overall_score >= 70
            else "needs improvement" if overall_score >= 50
            else "critical"
        )

        seo_issues = (seo.get("issues") or {}).get("items", [])
        perf_issues = (performance.get("issues") or {}).get("items", [])
        tech_issues = (technical.get("issues") or {}).get("items", [])

        executive = (
            f"We conducted a comprehensive digital audit of {name} ({url}). "
            f"The website achieved an overall score of {overall_score}/100, indicating {grade} health.\n\n"
            f"SEO scored {seo_score}/100 with {len(seo_issues)} issues. "
            f"Performance scored {perf_score}/100. Technical scored {tech_score}/100. "
            f"This report outlines findings and prioritized recommendations to improve visibility, "
            f"speed, security, and conversion potential."
        )

        seo_summary = self._section_summary(
            "SEO",
            seo_score,
            seo_issues,
            highlights=[
                f"Title: {seo.get('title_tag') or 'Missing'}",
                f"H1 count: {seo.get('h1_count', 'N/A')}",
                f"Broken links: {seo.get('broken_links', 0)}",
                f"Sitemap: {'Yes' if seo.get('has_sitemap') else 'No'}",
            ],
        )

        perf_summary = self._section_summary(
            "Performance",
            perf_score,
            perf_issues,
            highlights=[
                f"LCP: {performance.get('largest_contentful_paint') or 'N/A'} ms",
                f"FCP: {performance.get('first_contentful_paint') or 'N/A'} ms",
                f"Load time: {performance.get('load_time_ms') or 'N/A'} ms",
            ],
        )

        tech_summary = self._section_summary(
            "Technical",
            tech_score,
            tech_issues,
            highlights=[
                f"SSL valid: {'Yes' if technical.get('ssl_valid') else 'No'}",
                f"Mobile friendly: {'Yes' if technical.get('mobile_friendly') else 'No'}",
                f"Indexable: {'Yes' if technical.get('indexable', True) else 'No'}",
            ],
        )

        opp_lines = [
            o.get("title", o.get("code", "Issue"))
            for o in opportunities[:8]
        ] or self._opportunity_lines_from_issues(seo_issues, perf_issues, tech_issues)

        opportunity_summary = (
            f"{name} presents a {'high' if overall_score < 60 else 'moderate'} sales opportunity. "
            + ("Key gaps: " + "; ".join(opp_lines[:5]) + "." if opp_lines else "Incremental optimization recommended.")
        )
        if lead_classification:
            opportunity_summary += f" Lead priority: {lead_classification.upper()}."

        client_recs = self._build_client_recommendations(seo, performance, technical)
        talking_points = self._build_talking_points(name, overall_score, seo_issues, perf_issues, tech_issues)
        sales_pitch = (
            f"Hi, I'm reaching out because we audited {name}'s website and found {len(seo_issues + perf_issues + tech_issues)} "
            f"areas where improvements could drive more traffic and conversions. "
            f"Your overall score is {overall_score}/100 — we specialize in helping businesses like yours "
            f"fix SEO gaps, improve page speed, and strengthen technical security. "
            f"Would you be open to a 15-minute call to review the findings?"
        )
        outreach = self._build_outreach_recommendations(name, overall_score, lead_classification)

        return {
            "executive_summary": executive,
            "seo_summary": seo_summary,
            "performance_summary": perf_summary,
            "technical_summary": tech_summary,
            "opportunity_summary": opportunity_summary,
            "client_recommendations": client_recs,
            "cold_calling_talking_points": talking_points,
            "sales_pitch_summary": sales_pitch,
            "outreach_recommendations": outreach,
            "metadata": {"generated_by": "template", "model": None},
        }

    def _generate_with_openai(
        self,
        *,
        url: str,
        domain: str,
        company_name: str | None,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
        overall_score: float,
        opportunities: list[dict[str, Any]],
        lead_classification: str | None,
    ) -> dict[str, Any] | None:
        name = company_name or domain
        prompt = f"""Generate a website audit report as JSON for {name} ({url}).

Scores: Overall {overall_score}, SEO {seo.get('score')}, Performance {performance.get('score')}, Technical {technical.get('score')}.
SEO issues: {len((seo.get('issues') or {}).get('items', []))}
Performance issues: {len((performance.get('issues') or {}).get('items', []))}
Technical issues: {len((technical.get('issues') or {}).get('items', []))}
Opportunities: {[o.get('title') for o in opportunities[:5]]}
Lead class: {lead_classification or 'unknown'}

Return ONLY valid JSON with these keys:
- executive_summary (string, 2-3 paragraphs)
- seo_summary (string, 1 paragraph)
- performance_summary (string, 1 paragraph)
- technical_summary (string, 1 paragraph)
- opportunity_summary (string, 1 paragraph)
- client_recommendations (array of {{"title","description","priority"}})
- cold_calling_talking_points (array of strings, 5 items)
- sales_pitch_summary (string, 2-3 sentences)
- outreach_recommendations (array of {{"channel","message","timing"}})

Be professional, client-facing, and actionable."""

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a digital marketing auditor. Respond with valid JSON only.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                        "temperature": 0.4,
                        "response_format": {"type": "json_object"},
                    },
                )
                if response.status_code != 200:
                    logger.warning("openai_report_error", status=response.status_code)
                    return None
                import json

                raw = response.json()["choices"][0]["message"]["content"]
                data = json.loads(raw)
                data["metadata"] = {"generated_by": "openai", "model": settings.OPENAI_MODEL}
                return data
        except Exception as exc:
            logger.warning("openai_report_failed", error=str(exc))
            return None

    @staticmethod
    def _section_summary(
        label: str,
        score: float,
        issues: list[dict],
        highlights: list[str],
    ) -> str:
        status = "strong" if score >= 80 else "acceptable" if score >= 60 else "needs work"
        issue_text = f"{len(issues)} issue(s) identified" if issues else "no major issues"
        highlight_text = ". ".join(highlights)
        top_issues = "; ".join(i.get("message", "") for i in issues[:3])
        return (
            f"{label} performance is {status} at {score}/100 with {issue_text}. "
            f"{highlight_text}. "
            + (f"Top concerns: {top_issues}." if top_issues else "")
        )

    @staticmethod
    def _opportunity_lines_from_issues(
        seo: list, perf: list, tech: list
    ) -> list[str]:
        lines = []
        for issue in (seo + perf + tech)[:6]:
            if issue.get("severity") in ("critical", "high"):
                lines.append(issue.get("message", issue.get("code", "")))
        return lines

    @staticmethod
    def _build_client_recommendations(
        seo: dict, performance: dict, technical: dict
    ) -> list[dict[str, str]]:
        recs: list[dict[str, str]] = []
        seen: set[str] = set()
        for section in (seo, performance, technical):
            for item in (section.get("recommendations") or {}).get("items", []):
                title = item.get("title", "")
                if title and title not in seen:
                    seen.add(title)
                    recs.append({
                        "title": title,
                        "description": item.get("description", ""),
                        "priority": item.get("priority", "medium"),
                    })
        return recs[:12]

    @staticmethod
    def _build_talking_points(
        name: str,
        overall_score: float,
        seo_issues: list,
        perf_issues: list,
        tech_issues: list,
    ) -> list[str]:
        points = [
            f"We recently analyzed {name}'s website and scored it {overall_score}/100.",
        ]
        if seo_issues:
            points.append(f"We found {len(seo_issues)} SEO issues affecting search visibility.")
        if perf_issues:
            points.append("Page speed is slower than industry benchmarks — hurting conversions.")
        if tech_issues:
            points.append("There are technical security or SSL concerns worth addressing.")
        points.append("Businesses that fix these issues typically see improved traffic within 90 days.")
        points.append("We offer a free walkthrough of the full audit report — no obligation.")
        return points[:6]

    @staticmethod
    def _build_outreach_recommendations(
        name: str,
        overall_score: float,
        classification: str | None,
    ) -> list[dict[str, str]]:
        recs = [
            {
                "channel": "Email",
                "message": f"Subject: Quick audit findings for {name} — {overall_score}/100 score",
                "timing": "Send within 24 hours of audit completion",
            },
            {
                "channel": "Phone",
                "message": "Reference specific audit findings and offer a 15-minute review call.",
                "timing": "Follow up email 2-3 business days later if no response",
            },
        ]
        if classification == "hot":
            recs.insert(0, {
                "channel": "Priority",
                "message": f"{name} is a hot lead — prioritize immediate personalized outreach.",
                "timing": "Same day",
            })
        recs.append({
            "channel": "LinkedIn",
            "message": f"Connect with decision-maker and share one specific audit insight about {name}.",
            "timing": "Within first week",
        })
        return recs
