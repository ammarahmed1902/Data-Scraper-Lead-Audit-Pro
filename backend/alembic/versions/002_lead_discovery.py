"""Lead discovery schema migration

Revision ID: 002_lead_discovery
Revises: 001_initial
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_lead_discovery"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "lead_discovery_searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("industry_keyword", sa.String(255), nullable=False),
        sa.Column("country", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("total_found", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_duplicates", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_lead_discovery_searches_user_id", "lead_discovery_searches", ["user_id"])
    op.create_index("ix_lead_discovery_searches_status", "lead_discovery_searches", ["status"])
    op.create_index("ix_discovery_searches_user_created", "lead_discovery_searches", ["user_id", "created_at"])
    op.create_index("ix_lead_discovery_searches_celery_task_id", "lead_discovery_searches", ["celery_task_id"])

    op.create_table(
        "discovered_leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("lead_discovery_searches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("business_name", sa.String(500), nullable=False),
        sa.Column("website_url", sa.String(2048), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("business_category", sa.String(255), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("phone_number", sa.String(50), nullable=True),
        sa.Column("email_address", sa.String(255), nullable=True),
        sa.Column("social_profiles", postgresql.JSONB(), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("dedup_key", sa.String(255), nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("duplicate_of_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("discovered_leads.id", ondelete="SET NULL"), nullable=True),
        sa.Column("imported_website_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("websites.id", ondelete="SET NULL"), nullable=True),
        sa.Column("raw_data", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("search_id", "dedup_key", name="uq_discovered_leads_search_dedup"),
    )
    op.create_index("ix_discovered_leads_search_id", "discovered_leads", ["search_id"])
    op.create_index("ix_discovered_leads_user_id", "discovered_leads", ["user_id"])
    op.create_index("ix_discovered_leads_domain", "discovered_leads", ["domain"])
    op.create_index("ix_discovered_leads_dedup_key", "discovered_leads", ["dedup_key"])
    op.create_index("ix_discovered_leads_user_domain", "discovered_leads", ["user_id", "domain"])
    op.create_index("ix_discovered_leads_search_duplicate", "discovered_leads", ["search_id", "is_duplicate"])


def downgrade() -> None:
    op.drop_table("discovered_leads")
    op.drop_table("lead_discovery_searches")
