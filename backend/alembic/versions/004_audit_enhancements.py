"""Audit schema enhancements migration

Revision ID: 004_audit_enhancements
Revises: 003_business_enrichment
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_audit_enhancements"
down_revision: Union[str, None] = "003_business_enrichment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("seo_reports", sa.Column("h2_count", sa.Integer(), nullable=True))
    op.add_column("seo_reports", sa.Column("canonical_url", sa.String(2048), nullable=True))
    op.add_column(
        "performance_reports",
        sa.Column("issues", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "technical_reports",
        sa.Column("accessibility_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "technical_reports",
        sa.Column("mobile_friendly", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "technical_reports",
        sa.Column("indexable", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("technical_reports", "indexable")
    op.drop_column("technical_reports", "mobile_friendly")
    op.drop_column("technical_reports", "accessibility_score")
    op.drop_column("performance_reports", "issues")
    op.drop_column("seo_reports", "canonical_url")
    op.drop_column("seo_reports", "h2_count")
