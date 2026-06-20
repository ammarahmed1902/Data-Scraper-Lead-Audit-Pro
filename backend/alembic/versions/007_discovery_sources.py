"""Discovery source selection migration

Revision ID: 007_discovery_sources
Revises: 006_ai_report_content
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "007_discovery_sources"
down_revision: Union[str, None] = "006_ai_report_content"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE lead_discovery_searches "
        "ADD COLUMN IF NOT EXISTS data_source_category VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE lead_discovery_searches "
        "ADD COLUMN IF NOT EXISTS data_source_website VARCHAR(100)"
    )
    op.execute(
        "ALTER TABLE lead_discovery_searches "
        "ADD COLUMN IF NOT EXISTS source_search_url VARCHAR(2048)"
    )


def downgrade() -> None:
    op.drop_column("lead_discovery_searches", "source_search_url")
    op.drop_column("lead_discovery_searches", "data_source_website")
    op.drop_column("lead_discovery_searches", "data_source_category")
