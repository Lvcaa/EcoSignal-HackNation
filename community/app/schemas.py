"""Pydantic request/response schemas for community service."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class SubmitFootprintRequest(BaseModel):
    user_id: UUID
    zip_code: str
    kg_co2_week: float


class JoinChallengeRequest(BaseModel):
    user_id: UUID


class NeighborhoodStats(BaseModel):
    zip_code: str
    city: str | None
    avg_kg_co2_week: float
    participant_count: int
    your_kg_co2_week: float | None
    your_rank_pct: float | None
    better_than_pct: float | None


class ChallengeResponse(BaseModel):
    challenge_id: str
    title: str
    description: str
    category: str
    co2_saving_kg_week: float
    participant_count: int
    participant_target: int
    progress_pct: float
    user_joined: bool
    week_number: int


class ErrorResponse(BaseModel):
    detail: str
