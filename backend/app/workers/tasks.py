"""Celery background tasks."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import structlog

from app.core.config import settings
from app.core.sync_database import get_sync_session
from app.models.audit import AuditReport, AuditStatus
from app.services.audit_runner import AuditRunner
from app.services.export_runner import ExportRunner
from app.services.report_runner import ReportRunner
from app.workers.celery_worker import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="app.workers.tasks.run_audit", bind=True, max_retries=3)
def run_audit(self, audit_id: str):
    """Execute full website audit pipeline."""
    try:
        with get_sync_session() as session:
            runner = AuditRunner(session)
            audit = runner.run(uuid.UUID(audit_id))
            if audit.status == AuditStatus.FAILED.value:
                retry_count = (audit.raw_data or {}).get("retry_count", 0)
                if retry_count < settings.AUDIT_MAX_RETRIES:
                    audit.raw_data = {**(audit.raw_data or {}), "retry_count": retry_count + 1}
                    audit.status = AuditStatus.PENDING.value
                    audit.error_message = None
                    audit.completed_at = None
                    session.flush()
                    raise self.retry(countdown=60 * (retry_count + 1))
        return {"audit_id": audit_id, "status": "completed"}
    except self.MaxRetriesExceededError:
        logger.error("audit_max_retries_exceeded", audit_id=audit_id)
        raise
    except Exception as exc:
        logger.exception("audit_task_failed", audit_id=audit_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30)
        raise


@celery_app.task(name="app.workers.tasks.generate_report", bind=True, max_retries=2)
def generate_report(self, report_id: str):
    """Generate PDF/JSON report from audit data."""
    try:
        with get_sync_session() as session:
            ReportRunner(session).generate(report_id)
        return {"report_id": report_id, "status": "completed"}
    except Exception as exc:
        logger.exception("report_task_failed", report_id=report_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15)
        raise


@celery_app.task(name="app.workers.tasks.run_export", bind=True, max_retries=2)
def run_export(self, export_id: str):
    """Process data export job."""
    try:
        with get_sync_session() as session:
            ExportRunner(session).run(export_id)
        return {"export_id": export_id, "status": "completed"}
    except Exception as exc:
        logger.exception("export_task_failed", export_id=export_id)
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15)
        raise


@celery_app.task(name="app.workers.tasks.cleanup_expired_reports")
def cleanup_expired_reports():
    """Remove expired report files from storage."""
    from app.models.report import Report

    removed = 0
    with get_sync_session() as session:
        now = datetime.now(timezone.utc)
        reports = (
            session.query(Report)
            .filter(Report.expires_at.isnot(None), Report.expires_at < now)
            .all()
        )
        for report in reports:
            if report.file_path:
                path = Path(report.file_path)
                if path.exists():
                    path.unlink()
                    removed += 1
            session.delete(report)
    logger.info("cleanup_expired_reports", removed=removed)
    return {"removed": removed}


@celery_app.task(name="app.workers.tasks.retry_failed_audits")
def retry_failed_audits():
    """Re-queue failed audits eligible for retry."""
    from app.workers.tasks import run_audit as run_audit_task

    requeued = 0
    with get_sync_session() as session:
        audits = (
            session.query(AuditReport)
            .filter(AuditReport.status == AuditStatus.FAILED.value)
            .limit(50)
            .all()
        )
        for audit in audits:
            retry_count = (audit.raw_data or {}).get("retry_count", 0)
            if retry_count < settings.AUDIT_MAX_RETRIES:
                audit.status = AuditStatus.PENDING.value
                audit.error_message = None
                audit.completed_at = None
                session.flush()
                run_audit_task.delay(str(audit.id))
                requeued += 1
    logger.info("retry_failed_audits", requeued=requeued)
    return {"requeued": requeued}
