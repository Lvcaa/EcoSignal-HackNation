"""Pydantic schemas for footprint-engine service."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.enums import DietType, HomeType, TransportMode


def _most_recent_monday() -> date:
    """Return the most recent Monday (today if today is Monday)."""
    today = date.today()
    return today - timedelta(days=today.weekday())


# ── Request ──────────────────────────────────────────────────────


class FootprintRequest(BaseModel):
    """Input for the weekly footprint calculation."""

    user_id: UUID
    transport_mode: TransportMode
    diet_type: DietType
    home_type: HomeType
    home_size_sqm: int = Field(..., ge=10, le=1000)
    week_start: date = Field(default_factory=_most_recent_monday)


# ── Response ─────────────────────────────────────────────────────


class CategoryBreakdown(BaseModel):
    """CO₂ breakdown by category in kg, rounded to 2 decimal places."""

    model_config = ConfigDict(from_attributes=True)

    transport_kg: float = Field(..., description="kg CO₂e from transport")
    food_kg: float = Field(..., description="kg CO₂e from diet")
    home_kg: float = Field(..., description="kg CO₂e from home energy")


class FootprintResult(BaseModel):
    """Complete weekly footprint result returned to the caller."""

    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    week_start: date
    total_kg_co2: float = Field(
        ..., description="Sum of all categories, rounded to 2dp"
    )
    breakdown: CategoryBreakdown
    vs_national_avg_pct: float = Field(
        ...,
        description=(
            "Relative difference vs national average. "
            "e.g. -0.12 = 12% below average"
        ),
    )
    label: Literal["low", "average", "high", "very_high"] = Field(
        ...,
        description=(
            "low: <60% of avg, average: 60-110%, "
            "high: 110-150%, very_high: >150%"
        ),
    )


# ── Error ────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    detail: str
