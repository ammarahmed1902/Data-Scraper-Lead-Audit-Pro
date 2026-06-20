"""Repair missing audit columns when DB revision history diverged.

Revision ID: 009_audit_column_repair
Revises: 008_discovery_scrape_metadata
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "009_audit_column_repair"
down_revision: Union[str, None] = "008_discovery_scrape_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE technical_reports "
        "ADD COLUMN IF NOT EXISTS mobile_friendly BOOLEAN"
    )
    op.execute(
        "ALTER TABLE technical_reports "
        "ADD COLUMN IF NOT EXISTS indexable BOOLEAN"
    )
    op.execute(
        "ALTER TABLE technical_reports "
        "ADD COLUMN IF NOT EXISTS accessibility_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE performance_reports "
        "ADD COLUMN IF NOT EXISTS issues JSONB"
    )
    op.execute("ALTER TABLE seo_reports ADD COLUMN IF NOT EXISTS h2_count INTEGER")
    op.execute(
        "ALTER TABLE seo_reports "
        "ADD COLUMN IF NOT EXISTS canonical_url VARCHAR(2048)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE seo_reports DROP COLUMN IF EXISTS canonical_url")
    op.execute("ALTER TABLE seo_reports DROP COLUMN IF EXISTS h2_count")
    op.execute("ALTER TABLE performance_reports DROP COLUMN IF EXISTS issues")
    op.execute(
        "ALTER TABLE technical_reports DROP COLUMN IF EXISTS accessibility_score"
    )
    op.execute("ALTER TABLE technical_reports DROP COLUMN IF EXISTS indexable")
    op.execute("ALTER TABLE technical_reports DROP COLUMN IF EXISTS mobile_friendly")
