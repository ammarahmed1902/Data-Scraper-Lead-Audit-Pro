"""Business enrichment schema migration

Revision ID: 003_business_enrichment
Revises: 002_lead_discovery
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_business_enrichment"
down_revision: Union[str, None] = "002_lead_discovery"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "enrichment_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(50), nullable=False),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discovered_leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_discovery_searches.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_enrichment_jobs_user_id", "enrichment_jobs", ["user_id"])
    op.create_index("ix_enrichment_jobs_status", "enrichment_jobs", ["status"])
    op.create_index("ix_enrichment_jobs_user_created", "enrichment_jobs", ["user_id", "created_at"])
    op.create_index("ix_enrichment_jobs_celery_task_id", "enrichment_jobs", ["celery_task_id"])

    op.create_table(
        "business_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discovered_leads.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("enrichment_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("company_name", sa.String(500), nullable=True),
        sa.Column("about_us_content", sa.Text(), nullable=True),
        sa.Column("services", postgresql.JSONB(), nullable=True),
        sa.Column("contact_page_data", postgresql.JSONB(), nullable=True),
        sa.Column("email_addresses", postgresql.JSONB(), nullable=True),
        sa.Column("phone_numbers", postgresql.JSONB(), nullable=True),
        sa.Column("team_members", postgresql.JSONB(), nullable=True),
        sa.Column("business_description", sa.Text(), nullable=True),
        sa.Column("technology_stack", postgresql.JSONB(), nullable=True),
        sa.Column("cms_platform", sa.String(100), nullable=True),
        sa.Column("cms_detected", postgresql.JSONB(), nullable=True),
        sa.Column("pages_crawled", postgresql.JSONB(), nullable=True),
        sa.Column("raw_extraction", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("enriched_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_business_enrichments_lead_id", "business_enrichments", ["lead_id"])
    op.create_index("ix_business_enrichments_user_id", "business_enrichments", ["user_id"])
    op.create_index("ix_business_enrichments_status", "business_enrichments", ["status"])
    op.create_index("ix_business_enrichments_user_status", "business_enrichments", ["user_id", "status"])
    op.create_index("ix_business_enrichments_cms", "business_enrichments", ["cms_platform"])


def downgrade() -> None:
    op.drop_table("business_enrichments")
    op.drop_table("enrichment_jobs")
