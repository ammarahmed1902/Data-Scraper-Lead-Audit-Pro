"""Export repository."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export import ExportHistory
from app.repositories.base import BaseRepository


class ExportRepository(BaseRepository[ExportHistory]):
    def __init__(self, session: AsyncSession):
        super().__init__(ExportHistory, session)

    async def list_for_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> list[ExportHistory]:
        result = await self.session.execute(
            select(ExportHistory)
            .where(ExportHistory.user_id == user_id)
            .order_by(ExportHistory.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(ExportHistory)
            .where(ExportHistory.user_id == user_id)
        )
        return result.scalar_one()

    async def get_for_user(
        self, export_id: uuid.UUID, user_id: uuid.UUID
    ) -> ExportHistory | None:
        result = await self.session.execute(
            select(ExportHistory).where(
                ExportHistory.id == export_id, ExportHistory.user_id == user_id
            )
        )
        return result.scalar_one_or_none()
