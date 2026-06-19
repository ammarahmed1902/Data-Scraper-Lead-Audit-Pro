"""
Export endpoints.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_payload
from app.schemas.common import PaginatedResponse
from app.schemas.report import ExportCreate, ExportResponse
from app.services.export_service import ExportService

router = APIRouter()


def _user_id(payload: dict) -> uuid.UUID:
    return uuid.UUID(payload["sub"])


@router.get("", response_model=PaginatedResponse[ExportResponse])
async def list_exports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    return await service.list_exports(_user_id(payload), page, page_size)


@router.get("/{export_id}", response_model=ExportResponse)
async def get_export(
    export_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    export = await service.get_export(export_id, _user_id(payload))
    return ExportResponse.model_validate(export)


@router.post("", response_model=ExportResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export(
    data: ExportCreate,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    export = await service.create_export(
        _user_id(payload),
        data.export_type.value,
        data.format.value if hasattr(data.format, "value") else str(data.format),
        data.filters,
    )
    return ExportResponse.model_validate(export)


@router.get("/{export_id}/download")
async def download_export(
    export_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    export = await service.get_export(export_id, _user_id(payload))
    if export.status != "completed" or not export.file_path or not Path(export.file_path).exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not ready")
    return FileResponse(
        path=export.file_path,
        filename=Path(export.file_path).name,
        media_type="application/octet-stream",
    )


@router.delete("/{export_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_export(
    export_id: uuid.UUID,
    payload: dict = Depends(get_current_user_payload),
    db: AsyncSession = Depends(get_db),
):
    service = ExportService(db)
    await service.delete_export(export_id, _user_id(payload))
    return None
