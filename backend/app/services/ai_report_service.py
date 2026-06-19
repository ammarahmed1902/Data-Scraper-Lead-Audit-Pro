"""AI-powered and rule-based report summary generation."""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class AIReportService:
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
        if settings.OPENAI_API_KEY:
            ai_summary = self._generate_with_openai(
                url=url,
                domain=domain,
                company_name=company_name,
                seo=seo,
                performance=performance,
                technical=technical,
                overall_score=overall_score,
            )
            if ai_summary:
                return ai_summary
        return self._generate_template_summary(
            domain=domain,
            company_name=company_name,
            seo=seo,
            performance=performance,
            technical=technical,
            overall_score=overall_score,
        )

    def generate_sales_opportunity(
        self,
        *,
        domain: str,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
    ) -> str:
        opportunities: list[str] = []
        seo_issues = (seo.get("issues") or {}).get("items", [])
        perf_issues = (performance.get("issues") or {}).get("items", [])
        tech_issues = (technical.get("issues") or {}).get("items", [])

        critical = [i for i in seo_issues + perf_issues + tech_issues if i.get("severity") == "critical"]
        high = [i for i in seo_issues + perf_issues + tech_issues if i.get("severity") == "high"]

        if critical:
            opportunities.append(f"{len(critical)} critical issues require immediate attention")
        if high:
            opportunities.append(f"{len(high)} high-priority improvements identified")
        if seo.get("score", 100) < 70:
            opportunities.append("SEO optimization package — improve search visibility")
        if performance.get("score", 100) < 70:
            opportunities.append("Performance optimization — faster pages convert better")
        if technical.get("score", 100) < 70:
            opportunities.append("Technical remediation — security and compliance fixes")

        if not opportunities:
            return f"{domain} is in good health. Proactive monitoring and incremental optimization recommended."

        return f"Sales opportunity for {domain}: " + "; ".join(opportunities) + "."

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
    ) -> str | None:
        prompt = f"""Write a professional 3-paragraph executive summary for a website audit report.

Website: {url}
Company: {company_name or domain}
Overall Score: {overall_score}/100
SEO Score: {seo.get('score')}/100
Performance Score: {performance.get('score')}/100
Technical Score: {technical.get('score')}/100

SEO issues: {len((seo.get('issues') or {}).get('items', []))}
Performance issues: {len((performance.get('issues') or {}).get('items', []))}
Technical issues: {len((technical.get('issues') or {}).get('items', []))}

Include: executive overview, key findings, and recommended next steps. Be concise and client-ready."""

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": settings.OPENAI_MODEL,
                        "messages": [
                            {"role": "system", "content": "You are a professional digital marketing auditor."},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 600,
                        "temperature": 0.4,
                    },
                )
                if response.status_code != 200:
                    logger.warning("openai_api_error", status=response.status_code)
                    return None
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            logger.warning("openai_request_failed", error=str(exc))
            return None

    def _generate_template_summary(
        self,
        *,
        domain: str,
        company_name: str | None,
        seo: dict[str, Any],
        performance: dict[str, Any],
        technical: dict[str, Any],
        overall_score: float,
    ) -> str:
        name = company_name or domain
        seo_score = seo.get("score", 0)
        perf_score = performance.get("score", 0)
        tech_score = technical.get("score", 0)

        grade = "excellent" if overall_score >= 85 else "good" if overall_score >= 70 else "needs improvement" if overall_score >= 50 else "poor"

        p1 = (
            f"This audit of {name} ({domain}) achieved an overall score of {overall_score}/100, "
            f"indicating {grade} website health across SEO, performance, and technical dimensions."
        )
        p2 = (
            f"SEO scored {seo_score}/100 with {len((seo.get('issues') or {}).get('items', []))} issues identified. "
            f"Performance scored {perf_score}/100. Technical scored {tech_score}/100."
        )
        p3 = self.generate_sales_opportunity(
            domain=domain, seo=seo, performance=performance, technical=technical
        )
        return f"{p1}\n\n{p2}\n\n{p3}"
