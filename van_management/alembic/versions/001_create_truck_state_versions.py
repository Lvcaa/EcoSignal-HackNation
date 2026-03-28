"""Create truck_state_versions table

Revision ID: 001
Revises:
Create Date: 2026-03-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "truck_state_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("truck_id", sa.String(length=64), nullable=False),
        sa.Column(
            "waste_type",
            sa.Enum("organic", "paper", "plastic", "glass", "mixed", name="wastetype"),
            nullable=False,
        ),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("position_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("truck_id", "version", name="uq_truck_version"),
    )
    op.create_index("ix_truck_state_versions_truck_id", "truck_state_versions", ["truck_id"])
    op.create_index("ix_truck_version", "truck_state_versions", ["truck_id", "version"])
    op.create_index("ix_created_at", "truck_state_versions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_created_at", table_name="truck_state_versions")
    op.drop_index("ix_truck_version", table_name="truck_state_versions")
    op.drop_index("ix_truck_state_versions_truck_id", table_name="truck_state_versions")
    op.drop_table("truck_state_versions")
    op.execute("DROP TYPE IF EXISTS wastetype")
