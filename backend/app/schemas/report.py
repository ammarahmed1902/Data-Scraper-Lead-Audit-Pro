"""Report and export schemas."""

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from app.models.export import ExportStatus, ExportType
from app.models.report import ReportFormat, ReportStatus
from app.schemas.common import BaseSchema


class ReportCreate(BaseSchema):
    audit_report_id: uuid.UUID
    title: str = Field(..., max_length=500)
    format: ReportFormat = ReportFormat.PDF


class ReportResponse(BaseSchema):
    id: uuid.UUID
    audit_report_id: uuid.UUID
    user_id: uuid.UUID | None = None
    title: str
    format: ReportFormat
    status: ReportStatus
    file_path: str | None = None
    file_size_bytes: int | None = None
    error_message: str | None = None
    generated_at: datetime
    expires_at: datetime | None = None
    has_content: bool = False


class ReportContentResponse(BaseSchema):
    report_id: uuid.UUID
    audit_report_id: uuid.UUID
    title: str
    status: ReportStatus
    content: dict[str, Any]
    generated_at: datetime


class AuditReportCreate(BaseSchema):
    format: ReportFormat = ReportFormat.PDF


class ExportFormat(StrEnum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ExportCreate(BaseSchema):
    export_type: ExportType
    format: ExportFormat = ExportFormat.CSV
    filters: dict[str, Any] | None = None


class ExportResponse(BaseSchema):
    id: uuid.UUID
    export_type: ExportType
    format: str
    status: ExportStatus
    file_path: str | None = None
    file_size_bytes: int | None = None
    record_count: int | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
