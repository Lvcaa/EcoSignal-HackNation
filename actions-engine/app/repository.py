"""Database access layer for actions-engine."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ActionCompletion, ActionLog, UserStreak
from app.schemas import ActionLogResponse, StreakResponse


class ActionRepository:
    """Encapsulates all DB operations for actions and streaks."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_completed_today(self, user_id: UUID, today_rome: date) -> set[str]:
        """Return action_ids completed by this user on the given Rome date."""
        stmt = select(ActionCompletion.action_id).where(
            ActionCompletion.user_id == str(user_id),
            ActionCompletion.date_rome == today_rome,
        )
        result = await self.session.execute(stmt)
        return {row[0] for row in result.fetchall()}

    async def complete_action(
        self, user_id: UUID, action_id: str, now_rome: datetime
    ) -> tuple[ActionCompletion, bool]:
        """Insert completion if not already present (idempotent).

        Returns (completion, is_new) where is_new is False if already existed.
        """
        date_rome = now_rome.date()
        uid = str(user_id)

        # Check for existing completion (idempotency)
        stmt = select(ActionCompletion).where(
            ActionCompletion.user_id == uid,
            ActionCompletion.action_id == action_id,
            ActionCompletion.date_rome == date_rome,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            return existing, False

        completion = ActionCompletion(
            user_id=uid,
            action_id=action_id,
            completed_at=now_rome,
            date_rome=date_rome,
        )
        self.session.add(completion)
        await self.session.flush()
        return completion, True

    async def get_or_create_streak(self, user_id: UUID) -> UserStreak:
        """Get the streak row for a user, creating one if absent."""
        uid = str(user_id)
        stmt = select(UserStreak).where(UserStreak.user_id == uid)
        result = await self.session.execute(stmt)
        streak = result.scalar_one_or_none()

        if streak is not None:
            return streak

        streak = UserStreak(
            user_id=uid,
            current_streak=0,
            last_action_date=None,
            total_completions=0,
        )
        self.session.add(streak)
        await self.session.flush()
        return streak

    async def update_streak(
        self,
        user_id: UUID,
        new_streak: int,
        last_action_date: date,
        increment_total: bool,
    ) -> UserStreak:
        """Update the streak row with new values."""
        streak = await self.get_or_create_streak(user_id)
        streak.current_streak = new_streak
        streak.last_action_date = last_action_date
        if increment_total:
            streak.total_completions += 1
        await self.session.flush()
        return streak

    async def get_streak(self, user_id: UUID) -> StreakResponse:
        """Return StreakResponse for a user."""
        streak = await self.get_or_create_streak(user_id)
        return StreakResponse(
            user_id=user_id,
            current_streak=streak.current_streak,
            last_action_date=streak.last_action_date,
            total_completions=streak.total_completions,
        )

    # ── Action Log operations ─────────────────────────────────

    async def create_action_log(
        self,
        user_id: str,
        action_type: str,
        co2_delta_kg: float,
        description: str | None = None,
        image_analysis_id: str | None = None,
        metadata_json: dict | None = None,
        created_at: datetime | None = None,
    ) -> ActionLog:
        """Insert a new action log entry."""
        log = ActionLog(
            user_id=user_id,
            action_type=action_type,
            co2_delta_kg=co2_delta_kg,
            description=description,
            image_analysis_id=image_analysis_id,
            metadata_json=metadata_json,
        )
        if created_at is not None:
            log.created_at = created_at
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_actions_by_date(
        self, user_id: str, target_date: date
    ) -> list[ActionLog]:
        """Return all action logs for a user on a specific Rome date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        stmt = (
            select(ActionLog)
            .where(
                and_(
                    ActionLog.user_id == user_id,
                    ActionLog.created_at >= start,
                    ActionLog.created_at <= end,
                )
            )
            .order_by(ActionLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_actions_by_date_range(
        self, user_id: str, start_date: date, end_date: date
    ) -> list[ActionLog]:
        """Return all action logs for a user within a date range."""
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        stmt = (
            select(ActionLog)
            .where(
                and_(
                    ActionLog.user_id == user_id,
                    ActionLog.created_at >= start,
                    ActionLog.created_at <= end,
                )
            )
            .order_by(ActionLog.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
