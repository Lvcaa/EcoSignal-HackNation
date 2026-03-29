"""SQLAlchemy ORM models for user-profile service — source of truth."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, registry

mapper_registry = registry()


class Base(DeclarativeBase):
    registry = mapper_registry


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(128), nullable=False)
    zip_code: Mapped[str | None] = mapped_column(String(5), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    transport_mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    diet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    home_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    home_size_sqm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    commute_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_pets: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    pet_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    pet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    # TODO: add DB trigger for non-ORM updates
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def onboarding_complete(self) -> bool:
        return all(
            v is not None
            for v in [
                self.zip_code,
                self.transport_mode,
                self.diet_type,
                self.home_type,
                self.home_size_sqm,
                self.commute_days_per_week,
                self.has_pets,
            ]
        )
