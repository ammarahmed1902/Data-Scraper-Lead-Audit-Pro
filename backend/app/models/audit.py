"""
Audit and sub-report ORM models.
Tables: audit_reports, seo_reports, performance_reports, technical_reports
"""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AuditStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditReport(Base):
    __tablename__ = "audit_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    website_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50), default=AuditStatus.PENDING.value, nullable=False, index=True
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    website: Mapped["Website"] = relationship("Website", back_populates="audit_reports")
    created_by_user: Mapped["User"] = relationship("User", back_populates="audit_reports")
    seo_report: Mapped["SEOReport | None"] = relationship(
        "SEOReport", back_populates="audit_report", uselist=False, cascade="all, delete-orphan"
    )
    performance_report: Mapped["PerformanceReport | None"] = relationship(
        "PerformanceReport", back_populates="audit_report", uselist=False, cascade="all, delete-orphan"
    )
    technical_report: Mapped["TechnicalReport | None"] = relationship(
        "TechnicalReport", back_populates="audit_report", uselist=False, cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report", back_populates="audit_report", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_audit_reports_website_status", "website_id", "status"),
        Index("ix_audit_reports_created_at", "created_at"),
        Index("ix_audit_reports_overall_score", "overall_score"),
    )


class SEOReport(Base):
    __tablename__ = "seo_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    title_tag: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    internal_links: Mapped[int | None] = mapped_column(Integer, nullable=True)
    external_links: Mapped[int | None] = mapped_column(Integer, nullable=True)
    broken_links: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_sitemap: Mapped[bool | None] = mapped_column(nullable=True)
    has_robots_txt: Mapped[bool | None] = mapped_column(nullable=True)
    mobile_friendly: Mapped[bool | None] = mapped_column(nullable=True)
    issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    audit_report: Mapped["AuditReport"] = relationship("AuditReport", back_populates="seo_report")


class PerformanceReport(Base):
    __tablename__ = "performance_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    load_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    first_contentful_paint: Mapped[float | None] = mapped_column(Float, nullable=True)
    largest_contentful_paint: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_to_interactive: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_blocking_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    cumulative_layout_shift: Mapped[float | None] = mapped_column(Float, nullable=True)
    page_size_kb: Mapped[float | None] = mapped_column(Float, nullable=True)
    request_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    audit_report: Mapped["AuditReport"] = relationship(
        "AuditReport", back_populates="performance_report"
    )


class TechnicalReport(Base):
    __tablename__ = "technical_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    audit_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("audit_reports.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ssl_valid: Mapped[bool | None] = mapped_column(nullable=True)
    ssl_expiry: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    http_status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    server_header: Mapped[str | None] = mapped_column(String(255), nullable=True)
    technologies: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    security_headers: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    dns_records: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    issues: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    audit_report: Mapped["AuditReport"] = relationship(
        "AuditReport", back_populates="technical_report"
    )
