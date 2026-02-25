"""Add telegram_bot_token to users for optional OpenClaw Telegram channel.

Revision ID: 007
Revises: 006
Create Date: 2026-02-25

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("telegram_bot_token", sa.String(256), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "telegram_bot_token")
