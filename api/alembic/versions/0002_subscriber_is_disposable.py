"""Add subscriber.is_disposable.

Revision ID: 0002
Revises: 0001
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default backfills existing rows as not-disposable, which is the safe default:
    # nothing that already exists should become eligible for automatic deletion.
    op.add_column(
        "subscriber",
        sa.Column("is_disposable", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    # Dropped afterwards so the application, not the schema, decides the value on insert.
    op.alter_column("subscriber", "is_disposable", server_default=None)


def downgrade() -> None:
    op.drop_column("subscriber", "is_disposable")
