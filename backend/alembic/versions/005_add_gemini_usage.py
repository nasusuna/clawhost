"""Add gemini_usage table for per-instance monthly token tracking.

Revision ID: 005
Revises: 004
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gemini_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("instance_id", UUID(as_uuid=True), sa.ForeignKey("instances.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("tokens_used", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.create_unique_constraint("uq_gemini_usage_instance_period", "gemini_usage", ["instance_id", "period_start"])


def downgrade() -> None:
    op.drop_table("gemini_usage")
