"""Report generation service."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.audit import AuditStatus
from app.models.report import Report, ReportFormat
from app.repositories.report_repository import ReportRepository
from app.schemas.common import PaginatedResponse
from app.schemas.report import ReportResponse
from app.services.ai_report_service import AIReportService
from app.services.pdf_service import PDFService


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
    ) -> PaginatedResponse[ReportResponse]:
        skip = (page - 1) * page_size
        reports = await self.repo.list_for_owner(owner_id, skip, page_size, audit_id)
        total = await self.repo.count_for_owner(owner_id, audit_id)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[ReportResponse.model_validate(r) for r in reports],
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

        report = Report(
            audit_report_id=audit_report_id,
            title=title,
            format=format,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REPORT_EXPIRY_DAYS),
        )
        report = await self.repo.create(report)

        if settings.CELERY_TASK_ALWAYS_EAGER:
            from app.core.sync_database import get_sync_session
            from app.services.report_runner import ReportRunner

            with get_sync_session() as sync_session:
                ReportRunner(sync_session).generate(str(report.id))
            report = await self.get_report(report.id, owner_id)
        else:
            from app.workers.tasks import generate_report

            generate_report.delay(str(report.id))

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
        seo_data = {
            "score": seo.score if seo else None,
            "issues": seo.issues if seo else {},
            "recommendations": seo.recommendations if seo else {},
            "title_tag": seo.title_tag if seo else None,
            "meta_description": seo.meta_description if seo else None,
        }
        perf_data = {
            "score": perf.score if perf else None,
            "issues": {},
            "recommendations": perf.recommendations if perf else {},
            "metrics": perf.metrics if perf else {},
        }
        tech_data = {
            "score": tech.score if tech else None,
            "issues": tech.issues if tech else {},
            "recommendations": tech.recommendations if tech else {},
        }
        return {
            "overall_score": audit.overall_score,
            "summary": audit.summary,
            "seo_score": seo.score if seo else None,
            "performance_score": perf.score if perf else None,
            "technical_score": tech.score if tech else None,
            "seo": seo_data,
            "performance": perf_data,
            "technical": tech_data,
            "sales_opportunity": self.ai.generate_sales_opportunity(
                domain=audit.website.domain if audit.website else "",
                seo=seo_data,
                performance=perf_data,
                technical=tech_data,
            ),
        }
