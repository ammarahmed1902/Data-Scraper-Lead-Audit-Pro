"""
Report endpoints.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.report import (
    AuditReportCreate,
    ReportContentResponse,
    ReportCreate,
    ReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


def _to_response(report) -> ReportResponse:
    data = ReportResponse.model_validate(report)
    return data.model_copy(update={"has_content": bool(report.content)})


@router.get("", response_model=PaginatedResponse[ReportResponse])
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    audit_id: uuid.UUID | None = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    result = await service.list_reports(_user_id(payload), page, page_size, audit_id)
    return PaginatedResponse(
        items=[_to_response(r) for r in result.items],
        total=result.total,
        page=result.page,
        page_size=result.page_size,
        total_pages=result.total_pages,
    )


@router.post("", response_model=ReportResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_report(
    data: ReportCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    report = await service.create_report(
        data.audit_report_id,
        data.title,
        data.format.value,
        _user_id(payload),
    )
    return _to_response(report)


@router.post(
    "/audits/{audit_id}",
    response_model=ReportResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def generate_report_for_audit(
    audit_id: uuid.UUID,
    data: AuditReportCreate | None = None,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    fmt = data.format.value if data else "pdf"
    report = await service.create_for_audit(audit_id, _user_id(payload), fmt)
    return _to_response(report)


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    report = await service.get_report(report_id, _user_id(payload))
    return _to_response(report)


@router.get("/{report_id}/content", response_model=ReportContentResponse)
async def get_report_content(
    report_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    return await service.get_report_content(report_id, _user_id(payload))


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    report = await service.get_report(report_id, _user_id(payload))
    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not ready")
    media = "application/pdf" if report.format == "pdf" else "application/octet-stream"
    return FileResponse(
        path=report.file_path,
        filename=Path(report.file_path).name,
        media_type=media,
    )


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ReportService(db)
    await service.delete_report(report_id, _user_id(payload))
    return None
