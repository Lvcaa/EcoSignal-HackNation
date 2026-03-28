"""EcoSignal AI Narrative — Pydantic v2 request/response schemas."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from typing import Optional

from pydantic import BaseModel, Field

# ── Enums (local copy — no cross-service imports) ──────────────────


class TransportMode(StrEnum):
    car = "car"
    transit = "transit"
    bike = "bike"
    walk = "walk"
    mixed = "mixed"


class DietType(StrEnum):
    meat_daily = "meat_daily"
    meat_weekly = "meat_weekly"
    vegetarian = "vegetarian"
    vegan = "vegan"


class HomeType(StrEnum):
    apartment = "apartment"
    house = "house"


# ── Request ────────────────────────────────────────────────────────


class DailyAction(BaseModel):
    """A single logged daily action with its CO2 impact."""

    type: str  # meal | trip | grocery | clothing | appliance
    description: str
    co2_kg: float


class NarrativeRequest(BaseModel):
    """Aggregated data sent by api-gateway to generate a narrative."""

    user_id: UUID
    transport_mode: TransportMode
    diet_type: DietType
    home_type: HomeType
    home_size_sqm: int
    total_kg_co2: float
    vs_national_avg_pct: float
    breakdown: dict[str, float]  # transport_kg, food_kg, home_kg
    label: str  # low | average | high | very_high
    zip_code: str
    city: str | None = None
    pm25: float | None = None
    aqi_label: str  # good | moderate | unhealthy | hazardous
    current_temp_c: float | None = None
    anomaly_c: float | None = None
    anomaly_label: str | None = None
    air_is_fallback: bool = False
    climate_is_fallback: bool = False
    # Daily action tracking context
    daily_actions: list[DailyAction] = Field(default_factory=list)
    baseline_co2_kg: Optional[float] = None
    current_week_co2_kg: Optional[float] = None


# ── Response ───────────────────────────────────────────────────────


class NarrativeResponse(BaseModel):
    """Generated narrative returned to api-gateway."""

    user_id: UUID
    headline: str = Field(max_length=120)
    body: str
    local_context: str
    source_note: str
    generated_at: datetime
    is_fallback: bool = False


# ── Error ──────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    detail: str
