"""Add missing columns: address, latitude, longitude, commute_days_per_week, has_pets, pet_type, pet_count.

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-29
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("address", sa.String(300), nullable=True))
    op.add_column("users", sa.Column("latitude", sa.Float, nullable=True))
    op.add_column("users", sa.Column("longitude", sa.Float, nullable=True))


def downgrade() -> None:
    op.drop_column("users", "longitude")
    op.drop_column("users", "latitude")
    op.drop_column("users", "address")
