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


class WeeklySummaryEntry(BaseModel):
    action_type: ActionType
    count: int
    total_co2_delta_kg: float


class WeeklySummaryResponse(BaseModel):
    start_date: str
    end_date: str
    entries: list[WeeklySummaryEntry]
    total_co2_delta_kg: float
