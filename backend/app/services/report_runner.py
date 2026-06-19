"""Synchronous report generation for Celery workers."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy.orm import Session, selectinload

from app.models.audit import AuditReport
from app.models.report import Report, ReportFormat
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

        if report.format == ReportFormat.PDF.value:
            file_path, file_size = self.pdf.generate_audit_pdf(
                report_id=report.id,
                title=report.title,
                audit_data=audit_data,
            )
            report.file_path = file_path
            report.file_size_bytes = file_size
        elif report.format == ReportFormat.JSON.value:
            import json
            from pathlib import Path
            from app.core.config import settings

            storage = Path(settings.REPORT_STORAGE_PATH)
            storage.mkdir(parents=True, exist_ok=True)
            file_path = storage / f"report_{report.id}.json"
            file_path.write_text(json.dumps(audit_data, indent=2, default=str))
            report.file_path = str(file_path)
            report.file_size_bytes = file_path.stat().st_size

        report.generated_at = datetime.now(timezone.utc)
        self.session.flush()
        logger.info("report_generated", report_id=report_id, format=report.format)
        return report
