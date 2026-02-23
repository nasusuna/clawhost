"""Add gcp_project_id to subscriptions for one-project-per-subscription.

Revision ID: 006
Revises: 005
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("gcp_project_id", sa.String(64), nullable=True))
    op.create_index(op.f("ix_subscriptions_gcp_project_id"), "subscriptions", ["gcp_project_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_subscriptions_gcp_project_id"), table_name="subscriptions")
    op.drop_column("subscriptions", "gcp_project_id")
