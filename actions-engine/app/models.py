"""SQLAlchemy ORM models for actions-engine."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ActionCompletion(Base):
    """Records each action completion (one per user+action+day)."""

    __tablename__ = "action_completions"
    __table_args__ = (
        UniqueConstraint("user_id", "action_id", "date_rome", name="uq_user_action_date"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    action_id: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    date_rome: Mapped[date] = mapped_column(Date, nullable=False)


class UserStreak(Base):
    """Tracks current streak and total completions per user."""

    __tablename__ = "user_streaks"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_action_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    total_completions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )


class ActionLog(Base):
    """Logs individual user actions with CO2 delta tracking."""

    __tablename__ = "action_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    action_type: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    co2_delta_kg: Mapped[float] = mapped_column(Float, nullable=False)
    image_analysis_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
