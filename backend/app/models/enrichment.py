"""
Business enrichment ORM models (Phase 02).
Tables: enrichment_jobs, business_enrichments
"""

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EnrichmentStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EnrichmentJobType(StrEnum):
    SINGLE_LEAD = "single_lead"
    SEARCH_BULK = "search_bulk"


class EnrichmentJob(Base):
    __tablename__ = "enrichment_jobs"

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
        String(50), default=EnrichmentStatus.PENDING.value, nullable=False, index=True
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

    enrichments: Mapped[list["BusinessEnrichment"]] = relationship(
        "BusinessEnrichment", back_populates="job"
    )

    __table_args__ = (Index("ix_enrichment_jobs_user_created", "user_id", "created_at"),)


class BusinessEnrichment(Base):
    __tablename__ = "business_enrichments"

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
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("enrichment_jobs.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=EnrichmentStatus.PENDING.value, nullable=False, index=True
    )
    company_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    about_us_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    services: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    contact_page_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    email_addresses: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    phone_numbers: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    team_members: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    technology_stack: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    cms_platform: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cms_detected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    pages_crawled: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    raw_extraction: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    enriched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )

    job: Mapped["EnrichmentJob | None"] = relationship("EnrichmentJob", back_populates="enrichments")

    __table_args__ = (
        Index("ix_business_enrichments_user_status", "user_id", "status"),
        Index("ix_business_enrichments_cms", "cms_platform"),
    )
