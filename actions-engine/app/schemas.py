"""Pydantic schemas for actions-engine service."""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Enums (local copies — no cross-service imports) ─────────────


class ActionCategory(StrEnum):
    transport = "transport"
    food = "food"
    home = "home"
    community = "community"


class EffortLevel(StrEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# ── Core schemas ────────────────────────────────────────────────


class ActionItem(BaseModel):
    """One entry from the catalogue."""

    model_config = ConfigDict(from_attributes=True)

    action_id: str
    title: str
    description: str
    category: ActionCategory
    co2_saving_kg_week: float
    effort: EffortLevel


class ActionSuggestion(BaseModel):
    """Ranked action returned to the user."""

    action_id: str
    title: str
    description: str
    category: ActionCategory
    co2_saving_kg_week: float
    effort: EffortLevel
    completed_today: bool
    score: float = Field(description="Ranking score: co2_saving / effort_cost")


# ── Request / Response ──────────────────────────────────────────


class CompleteActionRequest(BaseModel):
    user_id: UUID


class CompleteActionResponse(BaseModel):
    action_id: str
    user_id: UUID
    completed_at: datetime
    streak_days: int
    message: str


class StreakResponse(BaseModel):
    user_id: UUID
    current_streak: int
    last_action_date: date | None
    total_completions: int


class ErrorResponse(BaseModel):
    detail: str


# ── Action Logging schemas ─────────────────────────────────


class ActionType(StrEnum):
    meal = "meal"
    trip = "trip"
    grocery = "grocery"
    clothing = "clothing"
    appliance = "appliance"


class LogActionRequest(BaseModel):
    user_id: UUID
    action_type: ActionType
    description: str | None = None
    co2_delta_kg: float
    image_analysis_id: str | None = None
    metadata: dict | None = None


class ActionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    action_type: ActionType
    description: str | None
    co2_delta_kg: float
    image_analysis_id: str | None
    metadata: dict | None
    created_at: datetime


class DailyActionsResponse(BaseModel):
    date: str
    actions: list[ActionLogResponse]
    total_co2_delta_kg: float


# ── Weekly Survey schemas ─────────────────────────────────


class WashingMachineTemp(StrEnum):
    cold = "cold"           # 30°C
    warm = "warm"           # 40°C
    hot = "hot"             # 60°C
    very_hot = "very_hot"   # 90°C


class DishwasherMode(StrEnum):
    eco = "eco"
    normal = "normal"
    intensive = "intensive"


class WeeklySurveyRequest(BaseModel):
    user_id: UUID
    washing_machine_cycles: int = Field(ge=0, le=14)
    washing_machine_temp: WashingMachineTemp = WashingMachineTemp.warm
    dishwasher_cycles: int = Field(ge=0, le=14)
    dishwasher_mode: DishwasherMode = DishwasherMode.normal
    week_start: date


class ApplianceCO2Breakdown(BaseModel):
    washing_machine_kg: float
    dishwasher_kg: float
    total_kg: float


class WeeklySurveyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    washing_machine_cycles: int
    washing_machine_temp: WashingMachineTemp
    dishwasher_cycles: int
    dishwasher_mode: DishwasherMode
    week_start: str
    co2_breakdown: ApplianceCO2Breakdown
    created_at: datetime


class WeeklySummaryEntry(BaseModel):
    action_type: ActionType
    count: int
    total_co2_delta_kg: float


class WeeklySummaryResponse(BaseModel):
    start_date: str
    end_date: str
    entries: list[WeeklySummaryEntry]
    total_co2_delta_kg: float
