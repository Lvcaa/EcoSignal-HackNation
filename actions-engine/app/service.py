"""Pure business logic — no FastAPI, no DB imports."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.models import ActionLog
from app.schemas import (
    ActionCategory,
    ActionItem,
    ActionLogResponse,
    ActionSuggestion,
    ActionType,
    ApplianceCO2Breakdown,
    DailyActionsResponse,
    DishwasherMode,
    EffortLevel,
    WashingMachineTemp,
    WeeklySummaryEntry,
    WeeklySummaryResponse,
    WeeklySurveyRequest,
    WeeklySurveyResponse,
)

ROME_TZ = ZoneInfo("Europe/Rome")

# ── Appliance CO2 factors (kg CO₂e per cycle) ────────────
# Duplicated from footprint-engine to avoid cross-service imports.

WASHING_MACHINE_CO2: dict[str, float] = {
    "cold": 0.3,
    "warm": 0.6,
    "hot": 1.0,
    "very_hot": 1.5,
}

DISHWASHER_CO2: dict[str, float] = {
    "eco": 0.4,
    "normal": 0.7,
    "intensive": 1.1,
}

EFFORT_COST: dict[EffortLevel, float] = {
    EffortLevel.easy: 1.0,
    EffortLevel.medium: 2.0,
    EffortLevel.hard: 4.0,
}


def rank_actions(
    all_actions: list[ActionItem],
    completed_today: set[str],
    category_filter: ActionCategory | None = None,
) -> list[ActionSuggestion]:
    """Rank actions by co2_saving / effort_cost. Returns top 10."""
    actions = all_actions
    if category_filter is not None:
        actions = [a for a in actions if a.category == category_filter]

    scored: list[ActionSuggestion] = []
    for action in actions:
        score = action.co2_saving_kg_week / EFFORT_COST[action.effort]
        scored.append(
            ActionSuggestion(
                action_id=action.action_id,
                title=action.title,
                description=action.description,
                category=action.category,
                co2_saving_kg_week=action.co2_saving_kg_week,
                effort=action.effort,
                completed_today=action.action_id in completed_today,
                score=round(score, 4),
            )
        )

    scored.sort(key=lambda s: s.score, reverse=True)
    return scored[:10]


def compute_streak(
    last_action_date: date | None,
    current_streak: int,
    today_rome: date,
) -> int:
    """Pure function: compute new streak value based on last action date."""
    if last_action_date is None:
        return 1
    if last_action_date == today_rome:
        return current_streak
    if last_action_date == today_rome - timedelta(days=1):
        return current_streak + 1
    return 1


def get_encouragement_message(streak_days: int) -> str:
    """Return an Italian encouragement message based on streak length."""
    if streak_days <= 1:
        return "Ottimo inizio! \U0001f331"
    if streak_days == 2:
        return "Due giorni di fila, continua così! \U0001f4aa"
    if streak_days <= 6:
        return f"\U0001f525 {streak_days} giorni di fila!"
    if streak_days <= 13:
        return "Una settimana intera! \U0001f3c6"
    if streak_days <= 29:
        return f"Incredibile, {streak_days} giorni! \U0001f30d"
    return "Un mese di impatto reale! \U0001f31f"


# ── Action Log helpers ─────────────────────────────────────


def _log_to_response(log: ActionLog) -> ActionLogResponse:
    """Convert an ActionLog ORM instance to its response schema."""
    return ActionLogResponse(
        id=log.id,
        user_id=log.user_id,
        action_type=ActionType(log.action_type),
        description=log.description,
        co2_delta_kg=log.co2_delta_kg,
        image_analysis_id=log.image_analysis_id,
        metadata=log.metadata_json,
        created_at=log.created_at,
    )


def build_daily_response(
    logs: list[ActionLog], target_date: date
) -> DailyActionsResponse:
    """Build a DailyActionsResponse from a list of ActionLog rows."""
    actions = [_log_to_response(log) for log in logs]
    total = sum(log.co2_delta_kg for log in logs)
    return DailyActionsResponse(
        date=target_date.isoformat(),
        actions=actions,
        total_co2_delta_kg=round(total, 4),
    )


# ── Weekly Survey helpers ──────────────────────────────────


def calculate_appliance_co2(req: WeeklySurveyRequest) -> ApplianceCO2Breakdown:
    """Calculate CO2 breakdown for weekly appliance survey."""
    wm_kg = round(
        req.washing_machine_cycles * WASHING_MACHINE_CO2[req.washing_machine_temp.value],
        4,
    )
    dw_kg = round(
        req.dishwasher_cycles * DISHWASHER_CO2[req.dishwasher_mode.value],
        4,
    )
    return ApplianceCO2Breakdown(
        washing_machine_kg=wm_kg,
        dishwasher_kg=dw_kg,
        total_kg=round(wm_kg + dw_kg, 4),
    )


def build_survey_response(log: ActionLog) -> WeeklySurveyResponse:
    """Build a WeeklySurveyResponse from an ActionLog with appliance metadata."""
    meta = log.metadata_json or {}
    co2 = meta.get("co2_breakdown", {})
    return WeeklySurveyResponse(
        id=log.id,
        user_id=log.user_id,
        washing_machine_cycles=meta.get("washing_machine_cycles", 0),
        washing_machine_temp=WashingMachineTemp(meta.get("washing_machine_temp", "warm")),
        dishwasher_cycles=meta.get("dishwasher_cycles", 0),
        dishwasher_mode=DishwasherMode(meta.get("dishwasher_mode", "normal")),
        week_start=meta.get("week_start", ""),
        co2_breakdown=ApplianceCO2Breakdown(
            washing_machine_kg=co2.get("washing_machine_kg", 0),
            dishwasher_kg=co2.get("dishwasher_kg", 0),
            total_kg=co2.get("total_kg", 0),
        ),
        created_at=log.created_at,
    )


def build_weekly_summary(
    logs: list[ActionLog], start_date: date, end_date: date
) -> WeeklySummaryResponse:
    """Aggregate action logs by action_type for a weekly summary."""
    by_type: dict[str, list[ActionLog]] = defaultdict(list)
    for log in logs:
        by_type[log.action_type].append(log)

    entries = []
    for action_type, type_logs in sorted(by_type.items()):
        entries.append(
            WeeklySummaryEntry(
                action_type=ActionType(action_type),
                count=len(type_logs),
                total_co2_delta_kg=round(
                    sum(l.co2_delta_kg for l in type_logs), 4
                ),
            )
        )

    total = sum(log.co2_delta_kg for log in logs)
    return WeeklySummaryResponse(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        entries=entries,
        total_co2_delta_kg=round(total, 4),
    )
