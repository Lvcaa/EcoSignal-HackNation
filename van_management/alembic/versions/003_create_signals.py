"""Create signals and signal_attachments tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-28
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "signal_type",
            sa.Enum("emergenza", "info", name="signaltype"),
            nullable=False,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_signals_signal_type", "signals", ["signal_type"])
    op.create_index("ix_signals_created_at", "signals", ["created_at"])

    op.create_table(
        "signal_attachments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("signal_id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["signal_id"], ["signals.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_signal_attachments_signal_id", "signal_attachments", ["signal_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_signal_attachments_signal_id", table_name="signal_attachments")
    op.drop_table("signal_attachments")
    op.drop_index("ix_signals_created_at", table_name="signals")
    op.drop_index("ix_signals_signal_type", table_name="signals")
    op.drop_table("signals")
    op.execute("DROP TYPE IF EXISTS signaltype")
