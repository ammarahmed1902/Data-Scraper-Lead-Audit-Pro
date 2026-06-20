"""Synchronous export processor for Celery workers."""

from __future__ import annotations

import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models.audit import AuditReport
from app.models.export import ExportHistory, ExportStatus, ExportType
from app.models.website import Website


class ExportRunner:
    def __init__(self, session):
        self.session = session
        self.storage = Path(settings.EXPORT_STORAGE_PATH)
        self.storage.mkdir(parents=True, exist_ok=True)

    def run(self, export_id: str) -> ExportHistory:
        export = self.session.get(ExportHistory, uuid.UUID(export_id))
        if export is None:
            raise ValueError(f"Export {export_id} not found")

        export.status = ExportStatus.PROCESSING.value
        export.started_at = datetime.now(UTC)
        self.session.flush()

        try:
            rows = self._collect_rows(export.user_id, export.export_type, export.filters or {})
            file_path, record_count = self._write_file(export, rows)
            export.file_path = file_path
            export.file_size_bytes = Path(file_path).stat().st_size
            export.record_count = record_count
            export.status = ExportStatus.COMPLETED.value
            export.completed_at = datetime.now(UTC)
        except Exception as exc:
            export.status = ExportStatus.FAILED.value
            export.error_message = str(exc)[:2000]
            export.completed_at = datetime.now(UTC)

        self.session.flush()
        return export

    def _collect_rows(self, user_id: uuid.UUID, export_type: str, filters: dict) -> list[dict]:
        if export_type == ExportType.AUDITS.value:
            return self._collect_audits(user_id, filters)
        return self._collect_leads(user_id, filters)

    def _collect_leads(self, user_id: uuid.UUID, filters: dict) -> list[dict]:
        websites = self.session.query(Website).filter(Website.owner_id == user_id).all()
        rows: list[dict] = []
        for site in websites:
            latest_audit = (
                self.session.query(AuditReport)
                .options(
                    selectinload(AuditReport.seo_report),
                    selectinload(AuditReport.performance_report),
                    selectinload(AuditReport.technical_report),
                )
                .filter(AuditReport.website_id == site.id, AuditReport.status == "completed")
                .order_by(AuditReport.completed_at.desc())
                .first()
            )
            row = {
                "website_id": str(site.id),
                "url": site.url,
                "domain": site.domain,
                "company_name": site.company_name or "",
                "contact_name": site.contact_name or "",
                "contact_email": site.contact_email or "",
                "contact_phone": site.contact_phone or "",
                "industry": site.industry or "",
                "website_status": site.status,
                "tags": site.tags or "",
                "last_audited_at": site.last_audited_at.isoformat() if site.last_audited_at else "",
                "audit_id": "",
                "overall_score": "",
                "seo_score": "",
                "performance_score": "",
                "technical_score": "",
                "audit_summary": "",
                "priority": self._priority_score(latest_audit),
            }
            if latest_audit:
                row.update({
                    "audit_id": str(latest_audit.id),
                    "overall_score": latest_audit.overall_score or "",
                    "seo_score": latest_audit.seo_report.score if latest_audit.seo_report else "",
                    "performance_score": latest_audit.performance_report.score if latest_audit.performance_report else "",
                    "technical_score": latest_audit.technical_report.score if latest_audit.technical_report else "",
                    "audit_summary": (latest_audit.summary or "")[:500],
                })
            rows.append(row)

        max_score = filters.get("max_score")
        if max_score is not None:
            rows = [
                r for r in rows
                if r.get("overall_score") != "" and float(r["overall_score"]) <= float(max_score)
            ]
        return rows

    def _collect_audits(self, user_id: uuid.UUID, filters: dict) -> list[dict]:
        audits = (
            self.session.query(AuditReport)
            .join(Website)
            .options(
                selectinload(AuditReport.seo_report),
                selectinload(AuditReport.performance_report),
                selectinload(AuditReport.technical_report),
                selectinload(AuditReport.website),
            )
            .filter(Website.owner_id == user_id)
            .order_by(AuditReport.created_at.desc())
            .all()
        )
        return [
            {
                "audit_id": str(a.id),
                "website_id": str(a.website_id),
                "domain": a.website.domain if a.website else "",
                "url": a.website.url if a.website else "",
                "status": a.status,
                "overall_score": a.overall_score or "",
                "seo_score": a.seo_report.score if a.seo_report else "",
                "performance_score": a.performance_report.score if a.performance_report else "",
                "technical_score": a.technical_report.score if a.technical_report else "",
                "created_at": a.created_at.isoformat(),
                "completed_at": a.completed_at.isoformat() if a.completed_at else "",
            }
            for a in audits
        ]

    def _priority_score(self, audit: AuditReport | None) -> str:
        if audit is None or audit.overall_score is None:
            return "unaudited"
        if audit.overall_score < 50:
            return "high"
        if audit.overall_score < 70:
            return "medium"
        return "low"

    def _write_file(self, export: ExportHistory, rows: list[dict]) -> tuple[str, int]:
        if not rows:
            rows = [{"message": "No records found"}]

        fmt = export.format.lower()
        if fmt == "xlsx":
            import openpyxl

            file_path = self.storage / f"export_{export.id}.xlsx"
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Export"
            headers = list(rows[0].keys())
            ws.append(headers)
            for row in rows:
                ws.append([row.get(h, "") for h in headers])
            wb.save(file_path)
        elif fmt == "json":
            file_path = self.storage / f"export_{export.id}.json"
            file_path.write_text(json.dumps(rows, indent=2, default=str))
        else:
            file_path = self.storage / f"export_{export.id}.csv"
            with open(file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)

        return str(file_path), len(rows)
