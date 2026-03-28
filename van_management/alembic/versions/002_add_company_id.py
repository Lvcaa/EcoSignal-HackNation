"""Add company_id to truck_state_versions

Revision ID: 002
Revises: 001
Create Date: 2026-03-28
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "truck_state_versions",
        sa.Column("company_id", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_company_id", "truck_state_versions", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_company_id", table_name="truck_state_versions")
    op.drop_column("truck_state_versions", "company_id")
