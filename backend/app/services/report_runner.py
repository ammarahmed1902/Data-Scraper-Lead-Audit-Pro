"""Synchronous AI report generation for Celery workers."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import structlog
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.audit import AuditReport
from app.models.lead_discovery import DiscoveredLead
from app.models.lead_scoring import LeadScore
from app.models.report import Report, ReportFormat, ReportStatus
from app.services.ai_report_service import AIReportService
from app.services.pdf_service import PDFService
from app.services.report_service import ReportService

logger = structlog.get_logger(__name__)


class ReportRunner:
    def __init__(self, session: Session):
        self.session = session
        self.pdf = PDFService()
        self.ai = AIReportService()

    def generate(self, report_id: str) -> Report:
        report = self.session.get(Report, uuid.UUID(report_id))
        if report is None:
            raise ValueError(f"Report {report_id} not found")

        report.status = ReportStatus.GENERATING.value
        report.error_message = None
        self.session.flush()

        try:
            audit = (
                self.session.query(AuditReport)
                .options(
                    selectinload(AuditReport.seo_report),
                    selectinload(AuditReport.performance_report),
                    selectinload(AuditReport.technical_report),
                    selectinload(AuditReport.website),
                )
                .filter(AuditReport.id == report.audit_report_id)
                .first()
            )
            if audit is None:
                raise ValueError("Audit not found for report")

            payload_builder = ReportService(self.session)  # type: ignore[arg-type]
            audit_data = payload_builder.build_audit_payload(audit)

            opportunities, classification = self._load_lead_context(audit.website_id)
            audit_data["ai_content"] = self.ai.generate_full_report(
                url=audit.website.url if audit.website else "",
                domain=audit.website.domain if audit.website else "",
                company_name=audit.website.company_name if audit.website else None,
                seo=audit_data["seo"],
                performance=audit_data["performance"],
                technical=audit_data["technical"],
                overall_score=audit.overall_score or 0,
                opportunities=opportunities,
                lead_classification=classification,
            )
            report.content = audit_data["ai_content"]

            if report.format == ReportFormat.PDF.value:
                file_path, file_size = self.pdf.generate_audit_pdf(
                    report_id=report.id,
                    title=report.title,
                    audit_data=audit_data,
                )
                report.file_path = file_path
                report.file_size_bytes = file_size
            elif report.format == ReportFormat.JSON.value:
                storage = Path(settings.REPORT_STORAGE_PATH)
                storage.mkdir(parents=True, exist_ok=True)
                file_path = storage / f"report_{report.id}.json"
                file_path.write_text(json.dumps(audit_data, indent=2, default=str))
                report.file_path = str(file_path)
                report.file_size_bytes = file_path.stat().st_size

            report.status = ReportStatus.COMPLETED.value
            report.generated_at = datetime.now(UTC)
            logger.info("report_generated", report_id=report_id, format=report.format)
        except Exception as exc:
            logger.exception("report_generation_failed", report_id=report_id)
            report.status = ReportStatus.FAILED.value
            report.error_message = str(exc)[:2000]

        self.session.flush()
        return report

    def _load_lead_context(self, website_id: uuid.UUID) -> tuple[list[dict], str | None]:
        lead = (
            self.session.query(DiscoveredLead)
            .filter(DiscoveredLead.imported_website_id == website_id)
            .first()
        )
        if lead is None:
            return [], None
        score = (
            self.session.query(LeadScore)
            .filter(LeadScore.lead_id == lead.id)
            .one_or_none()
        )
        if score is None:
            return [], None
        return score.opportunities or [], score.classification
