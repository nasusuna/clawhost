"""Add openrouter_api_key to instances.

Revision ID: 008
Revises: 007
Create Date: 2026-02-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("instances", sa.Column("openrouter_api_key", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("instances", "openrouter_api_key")
