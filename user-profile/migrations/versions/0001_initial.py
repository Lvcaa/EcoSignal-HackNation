"""Initial user table.

Revision ID: 0001
Revises:
Create Date: 2026-03-28
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("email", sa.String(254), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("hashed_password", sa.String(128), nullable=False),
        sa.Column("zip_code", sa.String(5), nullable=True),
        sa.Column("transport_mode", sa.String(20), nullable=True),
        sa.Column("diet_type", sa.String(20), nullable=True),
        sa.Column("home_type", sa.String(20), nullable=True),
        sa.Column("home_size_sqm", sa.Integer, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("users")
