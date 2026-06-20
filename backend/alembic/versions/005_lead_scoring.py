"""Lead scoring schema migration

Revision ID: 005_lead_scoring
Revises: 004_audit_enhancements
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_lead_scoring"
down_revision: Union[str, None] = "004_audit_enhancements"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scoring_jobs",
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
    op.create_index("ix_scoring_jobs_user_id", "scoring_jobs", ["user_id"])
    op.create_index("ix_scoring_jobs_status", "scoring_jobs", ["status"])
    op.create_index("ix_scoring_jobs_user_created", "scoring_jobs", ["user_id", "created_at"])

    op.create_table(
        "lead_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discovered_leads.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("audit_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("audit_reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("website_quality_score", sa.Float(), nullable=True),
        sa.Column("seo_opportunity_score", sa.Float(), nullable=True),
        sa.Column("technical_opportunity_score", sa.Float(), nullable=True),
        sa.Column("sales_potential_score", sa.Float(), nullable=True),
        sa.Column("composite_score", sa.Float(), nullable=True),
        sa.Column("classification", sa.String(20), nullable=False, server_default="cold"),
        sa.Column("opportunities", postgresql.JSONB(), nullable=True),
        sa.Column("opportunity_summary", postgresql.JSONB(), nullable=True),
        sa.Column("ranking", sa.Integer(), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_lead_scores_lead_id", "lead_scores", ["lead_id"])
    op.create_index("ix_lead_scores_user_id", "lead_scores", ["user_id"])
    op.create_index("ix_lead_scores_classification", "lead_scores", ["classification"])
    op.create_index("ix_lead_scores_composite", "lead_scores", ["composite_score"])
    op.create_index("ix_lead_scores_user_classification", "lead_scores", ["user_id", "classification"])
    op.create_index("ix_lead_scores_user_composite", "lead_scores", ["user_id", "composite_score"])


def downgrade() -> None:
    op.drop_table("lead_scores")
    op.drop_table("scoring_jobs")
