"""Discovery scrape metadata migration

Revision ID: 008_discovery_scrape_metadata
Revises: 007_discovery_sources
Create Date: 2026-06-20
"""

from typing import Sequence, Union

from alembic import op

revision: str = "008_discovery_scrape_metadata"
down_revision: Union[str, None] = "007_discovery_sources"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE discovered_leads "
        "ADD COLUMN IF NOT EXISTS profile_url VARCHAR(2048)"
    )
    op.execute(
        "ALTER TABLE discovered_leads "
        "ADD COLUMN IF NOT EXISTS scrape_status VARCHAR(50)"
    )
    op.execute(
        "ALTER TABLE discovered_leads "
        "ADD COLUMN IF NOT EXISTS scrape_errors JSONB"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_discovered_leads_scrape_status "
        "ON discovered_leads (scrape_status)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_discovered_leads_scrape_status")
    op.drop_column("discovered_leads", "scrape_errors")
    op.drop_column("discovered_leads", "scrape_status")
    op.drop_column("discovered_leads", "profile_url")
