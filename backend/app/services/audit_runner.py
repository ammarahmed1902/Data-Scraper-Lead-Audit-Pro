"""Synchronous audit pipeline executed by Celery workers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.orm import Session

from app.models.audit import (
    AuditReport,
    AuditStatus,
    PerformanceReport,
    SEOReport,
    TechnicalReport,
)
from app.models.website import Website, WebsiteStatus
from app.services.ai_report_service import AIReportService
from app.services.performance_service import PerformanceService
from app.services.scraper.page_fetcher import PageFetcher
from app.services.seo_service import SEOService
from app.services.technical_service import TechnicalService

logger = structlog.get_logger(__name__)


class AuditRunner:
    def __init__(self, session: Session):
        self.session = session
        self.fetcher = PageFetcher()
        self.seo = SEOService()
        self.performance = PerformanceService()
        self.technical = TechnicalService()
        self.ai = AIReportService()

    def run(self, audit_id: uuid.UUID) -> AuditReport:
        audit = self.session.get(AuditReport, audit_id)
        if audit is None:
            raise ValueError(f"Audit {audit_id} not found")

        if audit.status in (AuditStatus.COMPLETED.value, AuditStatus.CANCELLED.value):
            return audit

        website = self.session.get(Website, audit.website_id)
        if website is None:
            audit.status = AuditStatus.FAILED.value
            audit.error_message = "Website not found"
            audit.completed_at = datetime.now(timezone.utc)
            self.session.flush()
            return audit

        audit.status = AuditStatus.RUNNING.value
        audit.started_at = datetime.now(timezone.utc)
        audit.error_message = None
        website.status = WebsiteStatus.AUDITING.value
        self.session.flush()

        try:
            page = self.fetcher.fetch(website.url)
            seo_data = self.seo.analyze(website.url, page)
            perf_data = self.performance.analyze(website.url, page)
            tech_data = self.technical.analyze(website.url, page)

            self._save_seo_report(audit, seo_data)
            self._save_performance_report(audit, perf_data)
            self._save_technical_report(audit, tech_data)

            scores = [seo_data["score"], perf_data["score"], tech_data["score"]]
            audit.overall_score = round(sum(scores) / len(scores), 1)
            audit.summary = self.ai.generate_executive_summary(
                url=website.url,
                domain=website.domain,
                company_name=website.company_name,
                seo=seo_data,
                performance=perf_data,
                technical=tech_data,
                overall_score=audit.overall_score,
            )
            audit.raw_data = {
                "seo_score": seo_data["score"],
                "performance_score": perf_data["score"],
                "technical_score": tech_data["score"],
            }
            audit.status = AuditStatus.COMPLETED.value
            audit.completed_at = datetime.now(timezone.utc)
            website.status = WebsiteStatus.COMPLETED.value
            website.last_audited_at = audit.completed_at

            logger.info(
                "audit_completed",
                audit_id=str(audit_id),
                overall_score=audit.overall_score,
            )
        except Exception as exc:
            logger.exception("audit_failed", audit_id=str(audit_id))
            audit.status = AuditStatus.FAILED.value
            audit.error_message = str(exc)[:2000]
            audit.completed_at = datetime.now(timezone.utc)
            website.status = WebsiteStatus.FAILED.value
            retry_count = (audit.raw_data or {}).get("retry_count", 0)
            audit.raw_data = {**(audit.raw_data or {}), "retry_count": retry_count}

        self.session.flush()
        return audit

    def _save_seo_report(self, audit: AuditReport, data: dict) -> SEOReport:
        if audit.seo_report:
            report = audit.seo_report
        else:
            report = SEOReport(audit_report_id=audit.id)
            self.session.add(report)

        report.score = data.get("score")
        report.title_tag = data.get("title_tag")
        report.meta_description = data.get("meta_description")
        report.h1_count = data.get("h1_count")
        report.internal_links = data.get("internal_links")
        report.external_links = data.get("external_links")
        report.broken_links = data.get("broken_links")
        report.has_sitemap = data.get("has_sitemap")
        report.has_robots_txt = data.get("has_robots_txt")
        report.mobile_friendly = data.get("mobile_friendly")
        report.issues = data.get("issues")
        report.recommendations = data.get("recommendations")
        return report

    def _save_performance_report(self, audit: AuditReport, data: dict) -> PerformanceReport:
        if audit.performance_report:
            report = audit.performance_report
        else:
            report = PerformanceReport(audit_report_id=audit.id)
            self.session.add(report)

        report.score = data.get("score")
        report.load_time_ms = data.get("load_time_ms")
        report.first_contentful_paint = data.get("first_contentful_paint")
        report.largest_contentful_paint = data.get("largest_contentful_paint")
        report.time_to_interactive = data.get("time_to_interactive")
        report.total_blocking_time = data.get("total_blocking_time")
        report.cumulative_layout_shift = data.get("cumulative_layout_shift")
        report.page_size_kb = data.get("page_size_kb")
        report.request_count = data.get("request_count")
        report.metrics = data.get("metrics")
        report.recommendations = data.get("recommendations")
        return report

    def _save_technical_report(self, audit: AuditReport, data: dict) -> TechnicalReport:
        if audit.technical_report:
            report = audit.technical_report
        else:
            report = TechnicalReport(audit_report_id=audit.id)
            self.session.add(report)

        report.score = data.get("score")
        report.ssl_valid = data.get("ssl_valid")
        report.ssl_expiry = data.get("ssl_expiry")
        report.http_status_code = data.get("http_status_code")
        report.server_header = data.get("server_header")
        report.technologies = data.get("technologies")
        report.security_headers = data.get("security_headers")
        report.dns_records = data.get("dns_records")
        report.issues = data.get("issues")
        report.recommendations = data.get("recommendations")
        return report
