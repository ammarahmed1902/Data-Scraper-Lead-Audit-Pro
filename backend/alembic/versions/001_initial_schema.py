"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-06-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("timezone", sa.String(50), nullable=False, server_default="UTC"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_role_active", "users", ["role", "is_active"])

    op.create_table(
        "websites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(2048), nullable=False),
        sa.Column("domain", sa.String(255), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("contact_name", sa.String(255), nullable=True),
        sa.Column("contact_email", sa.String(255), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("last_audited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_websites_owner_id", "websites", ["owner_id"])
    op.create_index("ix_websites_domain", "websites", ["domain"])
    op.create_index("ix_websites_status", "websites", ["status"])
    op.create_index("ix_websites_owner_status", "websites", ["owner_id", "status"])
    op.create_index("ix_websites_created_at", "websites", ["created_at"])

    op.create_table(
        "audit_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("website_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("websites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_audit_reports_website_id", "audit_reports", ["website_id"])
    op.create_index("ix_audit_reports_created_by", "audit_reports", ["created_by"])
    op.create_index("ix_audit_reports_status", "audit_reports", ["status"])
    op.create_index("ix_audit_reports_celery_task_id", "audit_reports", ["celery_task_id"])
    op.create_index("ix_audit_reports_website_status", "audit_reports", ["website_id", "status"])
    op.create_index("ix_audit_reports_created_at", "audit_reports", ["created_at"])
    op.create_index("ix_audit_reports_overall_score", "audit_reports", ["overall_score"])

    op.create_table(
        "seo_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_reports.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("title_tag", sa.String(500), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("h1_count", sa.Integer(), nullable=True),
        sa.Column("internal_links", sa.Integer(), nullable=True),
        sa.Column("external_links", sa.Integer(), nullable=True),
        sa.Column("broken_links", sa.Integer(), nullable=True),
        sa.Column("has_sitemap", sa.Boolean(), nullable=True),
        sa.Column("has_robots_txt", sa.Boolean(), nullable=True),
        sa.Column("mobile_friendly", sa.Boolean(), nullable=True),
        sa.Column("issues", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "performance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_reports.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("load_time_ms", sa.Float(), nullable=True),
        sa.Column("first_contentful_paint", sa.Float(), nullable=True),
        sa.Column("largest_contentful_paint", sa.Float(), nullable=True),
        sa.Column("time_to_interactive", sa.Float(), nullable=True),
        sa.Column("total_blocking_time", sa.Float(), nullable=True),
        sa.Column("cumulative_layout_shift", sa.Float(), nullable=True),
        sa.Column("page_size_kb", sa.Float(), nullable=True),
        sa.Column("request_count", sa.Integer(), nullable=True),
        sa.Column("metrics", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "technical_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_reports.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("ssl_valid", sa.Boolean(), nullable=True),
        sa.Column("ssl_expiry", sa.DateTime(timezone=True), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column("server_header", sa.String(255), nullable=True),
        sa.Column("technologies", postgresql.JSONB(), nullable=True),
        sa.Column("security_headers", postgresql.JSONB(), nullable=True),
        sa.Column("dns_records", postgresql.JSONB(), nullable=True),
        sa.Column("issues", postgresql.JSONB(), nullable=True),
        sa.Column("recommendations", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("audit_report_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_reports.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("format", sa.String(20), nullable=False, server_default="pdf"),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_reports_audit_report_id", "reports", ["audit_report_id"])
    op.create_index("ix_reports_audit_format", "reports", ["audit_report_id", "format"])

    op.create_table(
        "export_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("export_type", sa.String(50), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("filters", postgresql.JSONB(), nullable=True),
        sa.Column("file_path", sa.String(1000), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("record_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_export_history_user_id", "export_history", ["user_id"])
    op.create_index("ix_export_history_export_type", "export_history", ["export_type"])
    op.create_index("ix_export_history_status", "export_history", ["status"])
    op.create_index("ix_export_history_user_status", "export_history", ["user_id", "status"])
    op.create_index("ix_export_history_created_at", "export_history", ["created_at"])


def downgrade() -> None:
    op.drop_table("export_history")
    op.drop_table("reports")
    op.drop_table("technical_reports")
    op.drop_table("performance_reports")
    op.drop_table("seo_reports")
    op.drop_table("audit_reports")
    op.drop_table("websites")
    op.drop_table("users")
