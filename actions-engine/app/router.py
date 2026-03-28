"""FastAPI router — thin controllers only."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Annotated
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.catalogue import get_action_by_id, get_all_actions
from app.repository import ActionRepository
from app.schemas import (
    ActionCategory,
    ActionSuggestion,
    CompleteActionRequest,
    CompleteActionResponse,
    DailyActionsResponse,
    ErrorResponse,
    LogActionRequest,
    StreakResponse,
    WeeklySummaryResponse,
    WeeklySurveyRequest,
    WeeklySurveyResponse,
)
from app.service import (
    build_daily_response,
    build_survey_response,
    build_weekly_summary,
    calculate_appliance_co2,
    compute_streak,
    get_encouragement_message,
    rank_actions,
)

ROME_TZ = ZoneInfo("Europe/Rome")

router = APIRouter(prefix="/actions", tags=["actions"])


async def _get_session() -> None:
    """Placeholder — overridden by app.main at startup."""
    raise RuntimeError("Session dependency not configured")  # pragma: no cover


async def get_repo(
    session: Annotated[AsyncSession, Depends(_get_session)],
) -> ActionRepository:
    """Dependency: create ActionRepository from session."""
    return ActionRepository(session)


# ── Annotated type aliases ──────────────────────────────────────

UserIdQuery = Annotated[UUID, Query(...)]
CategoryQuery = Annotated[ActionCategory | None, Query()]
RepoDep = Annotated[ActionRepository, Depends(get_repo)]


@router.get("", response_model=list[ActionSuggestion])
async def get_actions(
    user_id: UserIdQuery,
    repo: RepoDep,
    category: CategoryQuery = None,
) -> list[ActionSuggestion]:
    """Return top 3 ranked action suggestions for a user."""
    now_rome = datetime.now(tz=ROME_TZ)
    today_rome = now_rome.date()

    completed_today = await repo.get_completed_today(user_id, today_rome)
    suggestions = rank_actions(get_all_actions(), completed_today, category)
    return suggestions[:3]


@router.post(
    "/{action_id}/complete",
    response_model=CompleteActionResponse,
    responses={404: {"model": ErrorResponse}},
)
async def complete_action(
    action_id: str,
    body: CompleteActionRequest,
    repo: RepoDep,
) -> CompleteActionResponse:
    """Mark an action as completed for a user (idempotent per day)."""
    action = get_action_by_id(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")

    now_rome = datetime.now(tz=ROME_TZ)
    today_rome = now_rome.date()

    completion, is_new = await repo.complete_action(body.user_id, action_id, now_rome)

    streak_row = await repo.get_or_create_streak(body.user_id)
    new_streak = compute_streak(
        streak_row.last_action_date, streak_row.current_streak, today_rome
    )
    await repo.update_streak(body.user_id, new_streak, today_rome, increment_total=is_new)

    message = get_encouragement_message(new_streak)

    return CompleteActionResponse(
        action_id=action_id,
        user_id=body.user_id,
        completed_at=now_rome,
        streak_days=new_streak,
        message=message,
    )


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    user_id: UserIdQuery,
    repo: RepoDep,
) -> StreakResponse:
    """Return streak information for a user."""
    return await repo.get_streak(user_id)


# ── Action Logging endpoints ──────────────────────────────


@router.post("/log", response_model=DailyActionsResponse)
async def log_action(
    body: LogActionRequest,
    repo: RepoDep,
) -> DailyActionsResponse:
    """Log a new action with CO2 delta and return updated daily summary."""
    now_rome = datetime.now(tz=ROME_TZ)
    today_rome = now_rome.date()
    uid = str(body.user_id)

    await repo.create_action_log(
        user_id=uid,
        action_type=body.action_type.value,
        co2_delta_kg=body.co2_delta_kg,
        description=body.description,
        image_analysis_id=body.image_analysis_id,
        metadata_json=body.metadata,
        created_at=now_rome,
    )

    logs = await repo.get_actions_by_date(uid, today_rome)
    return build_daily_response(logs, today_rome)


@router.get("/daily", response_model=DailyActionsResponse)
async def get_daily_actions(
    user_id: UserIdQuery,
    repo: RepoDep,
    date_str: str | None = Query(None, alias="date"),
) -> DailyActionsResponse:
    """Return all actions logged by a user on a given date (defaults to today Rome)."""
    if date_str:
        try:
            target_date = date.fromisoformat(date_str)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid date format, use YYYY-MM-DD")
    else:
        target_date = datetime.now(tz=ROME_TZ).date()

    uid = str(user_id)
    logs = await repo.get_actions_by_date(uid, target_date)
    return build_daily_response(logs, target_date)


@router.get("/weekly", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    user_id: UserIdQuery,
    repo: RepoDep,
) -> WeeklySummaryResponse:
    """Return aggregated action summary for the current week (Mon-Sun Rome)."""
    today_rome = datetime.now(tz=ROME_TZ).date()
    start_of_week = today_rome - timedelta(days=today_rome.weekday())
    end_of_week = start_of_week + timedelta(days=6)

    uid = str(user_id)
    logs = await repo.get_actions_by_date_range(uid, start_of_week, end_of_week)
    return build_weekly_summary(logs, start_of_week, end_of_week)


# ── Weekly Survey endpoints ──────────────────────────────


@router.post("/weekly-survey", response_model=WeeklySurveyResponse)
async def submit_weekly_survey(
    body: WeeklySurveyRequest,
    repo: RepoDep,
) -> WeeklySurveyResponse:
    """Submit weekly appliance survey and calculate CO2."""
    now_rome = datetime.now(tz=ROME_TZ)
    uid = str(body.user_id)

    co2 = calculate_appliance_co2(body)

    # Delete previous appliance log for this week so re-submission replaces
    week_start = body.week_start
    week_end = week_start + timedelta(days=6)
    await repo.delete_appliance_logs_for_week(uid, week_start, week_end)

    log = await repo.create_action_log(
        user_id=uid,
        action_type="appliance",
        co2_delta_kg=co2.total_kg,
        description=f"Questionario settimanale elettrodomestici ({body.week_start})",
        metadata_json={
            "washing_machine_cycles": body.washing_machine_cycles,
            "washing_machine_temp": body.washing_machine_temp.value,
            "dishwasher_cycles": body.dishwasher_cycles,
            "dishwasher_mode": body.dishwasher_mode.value,
            "week_start": body.week_start.isoformat(),
            "co2_breakdown": co2.model_dump(),
        },
        created_at=now_rome,
    )

    return build_survey_response(log)


@router.get(
    "/weekly-survey/latest",
    response_model=WeeklySurveyResponse | None,
)
async def get_latest_survey(
    user_id: UserIdQuery,
    repo: RepoDep,
) -> WeeklySurveyResponse | None:
    """Return the most recent weekly appliance survey for a user."""
    uid = str(user_id)
    # Get recent appliance logs (last 30 days should cover it)
    today_rome = datetime.now(tz=ROME_TZ).date()
    start = today_rome - timedelta(days=30)
    logs = await repo.get_actions_by_date_range(uid, start, today_rome)
    appliance_logs = [l for l in logs if l.action_type == "appliance"]

    if not appliance_logs:
        return None

    # logs are already sorted by created_at desc
    return build_survey_response(appliance_logs[0])
