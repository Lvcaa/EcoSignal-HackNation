"""FastAPI router for community service endpoints."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app import repository as repo
from app.challenges import get_challenges
from app.schemas import (
    ChallengeResponse,
    JoinChallengeRequest,
    NeighborhoodStats,
    SubmitFootprintRequest,
)
from app.service import compute_neighborhood_stats, compute_progress_pct, get_active_challenge
from app.zip_mapping import get_city

ROME_TZ = ZoneInfo("Europe/Rome")

router = APIRouter(prefix="/community", tags=["community"])


async def _get_session() -> AsyncGenerator[AsyncSession, None]:
    """Placeholder — overridden by app.main at startup."""
    raise RuntimeError("Session dependency not configured")  # pragma: no cover
    yield  # noqa: RET504  # make it a generator


# ── Type aliases ──────────────────────────────────────────────

SessionDep = Annotated[AsyncSession, Depends(_get_session)]
UserIdQuery = Annotated[UUID, Query(...)]
ZipCodeQuery = Annotated[str, Query(...)]


def _current_week_year() -> tuple[int, int]:
    """Return (ISO week number, year) in Rome timezone."""
    now = datetime.now(tz=ROME_TZ)
    iso = now.isocalendar()
    return iso.week, iso.year


@router.post("/footprint/submit")
async def submit_footprint(
    body: SubmitFootprintRequest,
    session: SessionDep,
) -> dict[str, str]:
    """Submit an anonymized footprint for a ZIP code."""
    week, year = _current_week_year()
    await repo.submit_footprint(session, body.zip_code, body.kg_co2_week, week, year)
    await repo.upsert_user_footprint_ref(session, body.user_id, body.zip_code, body.kg_co2_week)
    return {"status": "submitted"}


@router.get("/stats", response_model=NeighborhoodStats)
async def get_stats(
    user_id: UserIdQuery,
    zip_code: ZipCodeQuery,
    session: SessionDep,
) -> NeighborhoodStats:
    """Get neighborhood stats for a ZIP code with optional user comparison."""
    week, year = _current_week_year()
    city = get_city(zip_code)
    footprints = await repo.get_zip_footprints(session, zip_code, week, year)
    user_ref = await repo.get_user_footprint_ref(session, user_id)
    user_kg = user_ref.last_kg_co2 if user_ref is not None else None
    return compute_neighborhood_stats(zip_code, city, footprints, user_kg)


@router.get("/challenge", response_model=ChallengeResponse)
async def get_challenge(
    user_id: UserIdQuery,
    session: SessionDep,
) -> ChallengeResponse:
    """Get the active weekly challenge."""
    week, year = _current_week_year()
    challenges = get_challenges()
    active = get_active_challenge(challenges, week)
    count = await repo.get_challenge_participant_count(
        session, active["challenge_id"], week, year
    )
    joined = await repo.is_user_joined(session, active["challenge_id"], user_id, week, year)
    return ChallengeResponse(
        challenge_id=active["challenge_id"],
        title=active["title"],
        description=active["description"],
        category=active["category"],
        co2_saving_kg_week=active["co2_saving_kg_week"],
        participant_count=count,
        participant_target=active["participant_target"],
        progress_pct=compute_progress_pct(count, active["participant_target"]),
        user_joined=joined,
        week_number=week,
    )


@router.post("/challenge/join", response_model=ChallengeResponse)
async def join_challenge(
    body: JoinChallengeRequest,
    session: SessionDep,
) -> ChallengeResponse:
    """Join the active weekly challenge (idempotent)."""
    week, year = _current_week_year()
    challenges = get_challenges()
    active = get_active_challenge(challenges, week)
    await repo.join_challenge(session, active["challenge_id"], body.user_id, week, year)
    count = await repo.get_challenge_participant_count(
        session, active["challenge_id"], week, year
    )
    return ChallengeResponse(
        challenge_id=active["challenge_id"],
        title=active["title"],
        description=active["description"],
        category=active["category"],
        co2_saving_kg_week=active["co2_saving_kg_week"],
        participant_count=count,
        participant_target=active["participant_target"],
        progress_pct=compute_progress_pct(count, active["participant_target"]),
        user_joined=True,
        week_number=week,
    )
