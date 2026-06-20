"""Auto-generate AI report after audit completion."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.report import Report, ReportFormat, ReportStatus
from app.services.report_runner import ReportRunner

logger = structlog.get_logger(__name__)


def auto_generate_report_for_audit(
    session: Session,
    audit_id: uuid.UUID,
    user_id: uuid.UUID,
    domain: str,
) -> Report | None:
    """Create and generate an AI report for a completed audit."""
    if not getattr(settings, "AUTO_GENERATE_REPORTS", True):
        return None

    existing = (
        session.query(Report)
        .filter(Report.audit_report_id == audit_id, Report.format == ReportFormat.PDF.value)
        .first()
    )
    if existing and existing.status == ReportStatus.COMPLETED.value:
        return existing

    report = Report(
        audit_report_id=audit_id,
        user_id=user_id,
        title=f"Website Audit Report — {domain}",
        format=ReportFormat.PDF.value,
        status=ReportStatus.PENDING.value,
        expires_at=datetime.now(UTC) + timedelta(days=settings.REPORT_EXPIRY_DAYS),
    )
    session.add(report)
    session.flush()

    try:
        if settings.CELERY_TASK_ALWAYS_EAGER:
            ReportRunner(session).generate(str(report.id))
        else:
            from app.workers.tasks import generate_report

            task = generate_report.delay(str(report.id))
            report.celery_task_id = task.id
            session.flush()
        logger.info("auto_report_generated", audit_id=str(audit_id), report_id=str(report.id))
        return report
    except Exception:
        logger.exception("auto_report_failed", audit_id=str(audit_id))
        report.status = ReportStatus.FAILED.value
        session.flush()
        return None
