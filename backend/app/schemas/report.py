"""Report and export schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from enum import Enum

from pydantic import Field

from app.models.export import ExportStatus, ExportType
from app.models.report import ReportFormat
from app.schemas.common import BaseSchema


class ReportCreate(BaseSchema):
    audit_report_id: uuid.UUID
    title: str = Field(..., max_length=500)
    format: ReportFormat = ReportFormat.PDF


class ReportResponse(BaseSchema):
    id: uuid.UUID
    audit_report_id: uuid.UUID
    title: str
    format: ReportFormat
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    generated_at: datetime
    expires_at: Optional[datetime] = None


class ExportFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ExportCreate(BaseSchema):
    export_type: ExportType
    format: ExportFormat = ExportFormat.CSV
    filters: Optional[Dict[str, Any]] = None


class ExportResponse(BaseSchema):
    id: uuid.UUID
    export_type: ExportType
    format: str
    status: ExportStatus
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    record_count: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
