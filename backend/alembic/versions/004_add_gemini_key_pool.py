"""Add gemini_key_pool table for pre-created keys assigned to new instances.

Revision ID: 004
Revises: 003
Create Date: 2026-02-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gemini_key_pool",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("api_key", sa.String(256), nullable=False),
        sa.Column("instance_id", UUID(as_uuid=True), sa.ForeignKey("instances.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("gemini_key_pool")
