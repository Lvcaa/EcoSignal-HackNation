"""SQLAlchemy ORM models for community service."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AnonymizedFootprint(Base):
    """Anonymized per-ZIP footprint submissions. No user_id — fully anonymized."""

    __tablename__ = "anonymized_footprints"
    __table_args__ = (
        UniqueConstraint(
            "zip_code", "week_number", "year", "id", name="uq_zip_week_year_id"
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    zip_code: Mapped[str] = mapped_column(String(5), index=True, nullable=False)
    kg_co2_week: Mapped[float] = mapped_column(Float, nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ChallengeParticipant(Base):
    """Tracks which users joined which challenge per week."""

    __tablename__ = "challenge_participants"
    __table_args__ = (
        UniqueConstraint(
            "challenge_id", "user_id", "week_number", "year",
            name="uq_challenge_user_week_year",
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    challenge_id: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False)
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class UserFootprintRef(Base):
    """Lightweight reference linking user_id to their latest footprint data."""

    __tablename__ = "user_footprint_refs"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str] = mapped_column(String(5), nullable=False)
    last_kg_co2: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
