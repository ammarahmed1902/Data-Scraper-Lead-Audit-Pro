"""Data export service."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.export import ExportHistory, ExportStatus
from app.repositories.export_repository import ExportRepository
from app.schemas.common import PaginatedResponse
from app.schemas.report import ExportResponse


class ExportService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ExportRepository(session)

    async def list_exports(
        self, user_id: uuid.UUID, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[ExportResponse]:
        skip = (page - 1) * page_size
        exports = await self.repo.list_for_user(user_id, skip, page_size)
        total = await self.repo.count_for_user(user_id)
        total_pages = max(1, (total + page_size - 1) // page_size)
        return PaginatedResponse(
            items=[ExportResponse.model_validate(e) for e in exports],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_export(self, export_id: uuid.UUID, user_id: uuid.UUID) -> ExportHistory:
        export = await self.repo.get_for_user(export_id, user_id)
        if export is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
        return export

    async def create_export(
        self,
        user_id: uuid.UUID,
        export_type: str,
        format: str,
        filters: dict | None = None,
    ) -> ExportHistory:
        export = ExportHistory(
            user_id=user_id,
            export_type=export_type,
            format=format,
            filters=filters,
            status=ExportStatus.PENDING.value,
        )
        export = await self.repo.create(export)

        if settings.CELERY_TASK_ALWAYS_EAGER:
            from app.core.sync_database import get_sync_session
            from app.services.export_runner import ExportRunner

            with get_sync_session() as sync_session:
                ExportRunner(sync_session).run(str(export.id))
            export = await self.get_export(export.id, user_id)
        else:
            from app.workers.tasks import run_export

            run_export.delay(str(export.id))

        return export

    async def delete_export(self, export_id: uuid.UUID, user_id: uuid.UUID) -> None:
        export = await self.get_export(export_id, user_id)
        if export.file_path:
            path = Path(export.file_path)
            if path.exists():
                path.unlink()
        await self.repo.delete(export)
