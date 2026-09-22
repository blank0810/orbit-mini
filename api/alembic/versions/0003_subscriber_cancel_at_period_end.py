"""Add subscriber.cancel_at_period_end.

Revision ID: 0003
Revises: 0002
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "subscriber",
        sa.Column("cancel_at_period_end", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("subscriber", "cancel_at_period_end", server_default=None)


def downgrade() -> None:
    op.drop_column("subscriber", "cancel_at_period_end")
