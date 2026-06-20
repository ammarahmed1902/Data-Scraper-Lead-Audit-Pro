"""AI report content schema migration

Revision ID: 006_ai_report_content
Revises: 005_lead_scoring
Create Date: 2026-06-20
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_ai_report_content"
down_revision: Union[str, None] = "005_lead_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("status", sa.String(50), nullable=False, server_default="pending"),
    )
    op.add_column("reports", sa.Column("content", postgresql.JSONB(), nullable=True))
    op.add_column("reports", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("reports", sa.Column("celery_task_id", sa.String(255), nullable=True))
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_status", "reports", ["status"])


def downgrade() -> None:
    op.drop_index("ix_reports_status", "reports")
    op.drop_index("ix_reports_user_id", "reports")
    op.drop_column("reports", "celery_task_id")
    op.drop_column("reports", "error_message")
    op.drop_column("reports", "content")
    op.drop_column("reports", "status")
    op.drop_column("reports", "user_id")
