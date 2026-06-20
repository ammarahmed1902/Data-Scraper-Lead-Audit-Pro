"""Extended audit report columns migration

Revision ID: 010_audit_extended_columns
Revises: 009_audit_column_repair
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "010_audit_extended_columns"
down_revision: Union[str, None] = "009_audit_column_repair"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS security_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS mobile_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS technical_seo_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS accessibility_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS conversion_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS lead_opportunity_score DOUBLE PRECISION"
    )
    op.execute(
        "ALTER TABLE audit_reports "
        "ADD COLUMN IF NOT EXISTS lead_classification VARCHAR(20)"
    )
    op.execute(
        "ALTER TABLE audit_reports ADD COLUMN IF NOT EXISTS sales_summary TEXT"
    )
    op.execute(
        "ALTER TABLE audit_reports ADD COLUMN IF NOT EXISTS category_breakdown JSONB"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_audit_reports_lead_classification "
        "ON audit_reports (lead_classification)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_audit_reports_lead_classification")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS category_breakdown")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS sales_summary")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS lead_classification")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS lead_opportunity_score")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS conversion_score")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS accessibility_score")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS technical_seo_score")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS mobile_score")
    op.execute("ALTER TABLE audit_reports DROP COLUMN IF EXISTS security_score")
