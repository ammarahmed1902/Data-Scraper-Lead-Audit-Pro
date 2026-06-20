"""Tests for report generation service."""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.audit import AuditReport, AuditStatus
from app.models.report import ReportStatus
from app.services.report_service import ReportService


@pytest_asyncio.fixture
async def completed_audit() -> tuple[uuid.UUID, uuid.UUID]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(AuditReport)
            .where(AuditReport.status == AuditStatus.COMPLETED.value)
            .limit(1)
        )
        audit = result.scalar_one_or_none()
        if audit is None:
            pytest.skip("No completed audit in database")
        return audit.id, audit.created_by


@pytest.mark.asyncio
async def test_create_for_audit_does_not_raise_missing_greenlet(completed_audit):
    audit_id, owner_id = completed_audit
    async with async_session_factory() as session:
        report = await ReportService(session).create_for_audit(audit_id, owner_id)
        assert report.id is not None
        assert report.status in (
            ReportStatus.COMPLETED.value,
            ReportStatus.PENDING.value,
            ReportStatus.GENERATING.value,
        )
