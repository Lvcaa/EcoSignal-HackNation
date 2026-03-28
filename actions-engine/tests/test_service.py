"""Pure unit tests for service.py — no DB, no HTTP."""

from __future__ import annotations

from datetime import date

from app.catalogue import get_all_actions
from app.schemas import ActionCategory, ActionItem, EffortLevel
from app.service import compute_streak, get_encouragement_message, rank_actions


def _make_action(
    action_id: str = "test_01",
    category: ActionCategory = ActionCategory.transport,
    co2: float = 4.0,
    effort: EffortLevel = EffortLevel.easy,
) -> ActionItem:
    return ActionItem(
        action_id=action_id,
        title="Test",
        description="Test action",
        category=category,
        co2_saving_kg_week=co2,
        effort=effort,
    )


# ── rank_actions ────────────────────────────────────────────────


class TestRankActions:
    def test_returns_at_most_10(self) -> None:
        actions = get_all_actions()
        result = rank_actions(actions, set())
        assert len(result) <= 10

    def test_completed_today_flag(self) -> None:
        actions = get_all_actions()
        completed = {actions[0].action_id}
        result = rank_actions(actions, completed)
        ids_completed = {s.action_id for s in result if s.completed_today}
        assert actions[0].action_id in ids_completed

    def test_scores_computed_correctly(self) -> None:
        actions = [
            _make_action("a", co2=4.0, effort=EffortLevel.easy),   # 4.0/1.0 = 4.0
            _make_action("b", co2=4.0, effort=EffortLevel.medium), # 4.0/2.0 = 2.0
            _make_action("c", co2=4.0, effort=EffortLevel.hard),   # 4.0/4.0 = 1.0
        ]
        result = rank_actions(actions, set())
        assert result[0].score == 4.0
        assert result[1].score == 2.0
        assert result[2].score == 1.0

    def test_sorted_by_score_descending(self) -> None:
        actions = get_all_actions()
        result = rank_actions(actions, set())
        scores = [s.score for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_category_filter(self) -> None:
        actions = get_all_actions()
        result = rank_actions(actions, set(), category_filter=ActionCategory.transport)
        assert all(s.category == ActionCategory.transport for s in result)

    def test_empty_completed_set(self) -> None:
        actions = get_all_actions()
        result = rank_actions(actions, set())
        assert all(not s.completed_today for s in result)

    def test_all_completed(self) -> None:
        actions = get_all_actions()
        all_ids = {a.action_id for a in actions}
        result = rank_actions(actions, all_ids)
        assert all(s.completed_today for s in result)


# ── compute_streak ──────────────────────────────────────────────


class TestComputeStreak:
    def test_first_action(self) -> None:
        assert compute_streak(None, 0, date(2026, 3, 28)) == 1

    def test_same_day(self) -> None:
        today = date(2026, 3, 28)
        assert compute_streak(today, 5, today) == 5

    def test_next_day(self) -> None:
        yesterday = date(2026, 3, 27)
        today = date(2026, 3, 28)
        assert compute_streak(yesterday, 3, today) == 4

    def test_gap_two_days(self) -> None:
        two_ago = date(2026, 3, 26)
        today = date(2026, 3, 28)
        assert compute_streak(two_ago, 10, today) == 1

    def test_gap_thirty_days(self) -> None:
        old = date(2026, 2, 26)
        today = date(2026, 3, 28)
        assert compute_streak(old, 15, today) == 1


# ── get_encouragement_message ───────────────────────────────────


class TestGetEncouragementMessage:
    def test_streak_1(self) -> None:
        assert "inizio" in get_encouragement_message(1).lower()

    def test_streak_3(self) -> None:
        assert "3" in get_encouragement_message(3)

    def test_streak_7(self) -> None:
        assert "settimana" in get_encouragement_message(7).lower()

    def test_streak_30(self) -> None:
        assert "mese" in get_encouragement_message(30).lower()
