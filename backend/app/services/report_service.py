"""Report generation service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit import AuditStatus
from app.models.report import Report, ReportFormat, ReportStatus
from app.repositories.report_repository import ReportRepository
from app.schemas.common import PaginatedResponse
from app.schemas.report import ReportContentResponse, ReportResponse
from app.services.ai_report_service import AIReportService
from app.services.pdf_service import PDFService

logger = structlog.get_logger(__name__)


class ReportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ReportRepository(session)
        self.ai = AIReportService()
        self.pdf = PDFService()

    async def list_reports(
        self,
        owner_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        audit_id: uuid.UUID | None = None,
    ) -> PaginatedResponse[Report]:
        skip = (page - 1) * page_size
        reports = await self.repo.list_for_owner(owner_id, skip, page_size, audit_id)
        total = await self.repo.count_for_owner(owner_id, audit_id)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=reports,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_report(self, report_id: uuid.UUID, owner_id: uuid.UUID) -> Report:
        report = await self.repo.get_for_owner(report_id, owner_id)
        if report is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
        return report

    async def get_report_content(
        self, report_id: uuid.UUID, owner_id: uuid.UUID
    ) -> ReportContentResponse:
        report = await self.get_report(report_id, owner_id)
        if not report.content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report content not yet generated",
            )
        return ReportContentResponse(
            report_id=report.id,
            audit_report_id=report.audit_report_id,
            title=report.title,
            status=report.status,
            content=report.content,
            generated_at=report.generated_at,
        )

    async def create_report(
        self,
        audit_report_id: uuid.UUID,
        title: str,
        format: str,
        owner_id: uuid.UUID,
    ) -> Report:
        audit = await self.repo.get_audit_for_owner(audit_report_id, owner_id)
        if audit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
        if audit.status != AuditStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit must be completed before generating a report",
            )
        return await self._create_and_queue(
            audit_report_id=audit_report_id,
            title=title,
            format=format,
            owner_id=owner_id,
            website=audit.website,
        )

    async def create_for_audit(
        self,
        audit_report_id: uuid.UUID,
        owner_id: uuid.UUID,
        format: str = ReportFormat.PDF.value,
    ) -> Report:
        audit = await self.repo.get_audit_for_owner(audit_report_id, owner_id)
        if audit is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit not found")
        if audit.status != AuditStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Audit must be completed before generating a report",
            )
        domain = audit.website.domain if audit.website else "Website"
        title = f"Website Audit Report — {domain}"
        return await self._create_and_queue(
            audit_report_id=audit_report_id,
            title=title,
            format=format,
            owner_id=owner_id,
            website=audit.website,
        )

    async def _create_and_queue(
        self,
        *,
        audit_report_id: uuid.UUID,
        title: str,
        format: str,
        owner_id: uuid.UUID,
        website,
    ) -> Report:
        report = Report(
            audit_report_id=audit_report_id,
            user_id=owner_id,
            title=title,
            format=format,
            status=ReportStatus.PENDING.value,
            expires_at=datetime.now(UTC) + timedelta(days=settings.REPORT_EXPIRY_DAYS),
        )
        report = await self.repo.create(report)
        await self.session.commit()
        report_id = report.id

        from app.workers.tasks import generate_report as generate_report_task

        if settings.CELERY_TASK_ALWAYS_EAGER:
            from app.core.sync_database import get_sync_session
            from app.services.report_runner import ReportRunner

            try:
                with get_sync_session() as sync_session:
                    ReportRunner(sync_session).generate(str(report_id))
                self.session.expunge(report)
                report = await self.get_report(report_id, owner_id)
                logger.info("report_generated_inline", report_id=str(report_id), status=report.status)
            except Exception as exc:
                logger.exception("report_inline_generation_failed", report_id=str(report_id))
                self.session.expunge(report)
                report = await self.get_report(report_id, owner_id)
                if report.status != ReportStatus.FAILED.value:
                    report.status = ReportStatus.FAILED.value
                    report.error_message = str(exc)[:500]
                    report = await self.repo.update(report)
                    await self.session.commit()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Report generation failed: {exc}",
                ) from exc
        else:
            try:
                task = generate_report_task.delay(str(report.id))
                report.celery_task_id = task.id
                report = await self.repo.update(report)
                await self.session.commit()
                logger.info("report_queued", report_id=str(report.id), celery_task_id=task.id)
            except Exception as exc:
                logger.exception("report_queue_failed", report_id=str(report.id))
                report.status = ReportStatus.FAILED.value
                report.error_message = f"Queue dispatch failed: {exc}"[:500]
                await self.repo.update(report)
                await self.session.commit()
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Report created but background worker unavailable.",
                ) from exc

        return report

    async def delete_report(self, report_id: uuid.UUID, owner_id: uuid.UUID) -> None:
        report = await self.get_report(report_id, owner_id)
        if report.file_path:
            from pathlib import Path

            path = Path(report.file_path)
            if path.exists():
                path.unlink()
        await self.repo.delete(report)

    def build_audit_payload(self, audit) -> dict:
        seo = audit.seo_report
        perf = audit.performance_report
        tech = audit.technical_report
        website = audit.website

        seo_data = {
            "score": seo.score if seo else None,
            "issues": seo.issues if seo else {},
            "recommendations": seo.recommendations if seo else {},
            "title_tag": seo.title_tag if seo else None,
            "meta_description": seo.meta_description if seo else None,
            "h1_count": seo.h1_count if seo else None,
            "broken_links": seo.broken_links if seo else None,
            "has_sitemap": seo.has_sitemap if seo else None,
        }
        perf_data = {
            "score": perf.score if perf else None,
            "issues": perf.issues if perf else {},
            "recommendations": perf.recommendations if perf else {},
            "metrics": perf.metrics if perf else {},
            "largest_contentful_paint": perf.largest_contentful_paint if perf else None,
            "first_contentful_paint": perf.first_contentful_paint if perf else None,
            "load_time_ms": perf.load_time_ms if perf else None,
        }
        tech_data = {
            "score": tech.score if tech else None,
            "issues": tech.issues if tech else {},
            "recommendations": tech.recommendations if tech else {},
            "ssl_valid": tech.ssl_valid if tech else None,
            "mobile_friendly": tech.mobile_friendly if tech else None,
            "indexable": tech.indexable if tech else None,
        }

        ai_content = None
        if audit.summary:
            ai_content = {"executive_summary": audit.summary}

        return {
            "url": website.url if website else "",
            "domain": website.domain if website else "",
            "company_name": website.company_name if website else None,
            "overall_score": audit.overall_score,
            "summary": audit.summary,
            "seo_score": seo.score if seo else None,
            "performance_score": perf.score if perf else None,
            "technical_score": tech.score if tech else None,
            "seo": seo_data,
            "performance": perf_data,
            "technical": tech_data,
            "ai_content": ai_content,
        }
