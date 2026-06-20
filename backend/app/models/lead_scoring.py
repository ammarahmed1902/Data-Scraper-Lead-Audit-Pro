"""
Lead scoring ORM models (Phase 04).
Tables: scoring_jobs, lead_scores
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class LeadClassification(StrEnum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class ScoringJobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScoringJobType(StrEnum):
    SINGLE_LEAD = "single_lead"
    SEARCH_BULK = "search_bulk"
    RESCORE_ALL = "rescore_all"


class ScoringJob(Base):
    __tablename__ = "scoring_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("discovered_leads.id", ondelete="SET NULL"), nullable=True
    )
    search_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("lead_discovery_searches.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50), default=ScoringJobStatus.PENDING.value, nullable=False, index=True
    )
    total_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_leads: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (Index("ix_scoring_jobs_user_created", "user_id", "created_at"),)


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lead_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discovered_leads.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    audit_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id", ondelete="SET NULL"), nullable=True
    )
    website_quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    seo_opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    technical_opportunity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    sales_potential_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    composite_score: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    classification: Mapped[str] = mapped_column(
        String(20), default=LeadClassification.COLD.value, nullable=False, index=True
    )
    opportunities: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    opportunity_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ranking: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_lead_scores_user_classification", "user_id", "classification"),
        Index("ix_lead_scores_user_composite", "user_id", "composite_score"),
    )
