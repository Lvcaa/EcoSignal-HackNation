"""Database access layer for community service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AnonymizedFootprint, ChallengeParticipant, UserFootprintRef

ROME_TZ = ZoneInfo("Europe/Rome")


async def submit_footprint(
    session: AsyncSession,
    zip_code: str,
    kg_co2: float,
    week: int,
    year: int,
) -> None:
    """Insert an anonymized footprint record (no user_id)."""
    record = AnonymizedFootprint(
        zip_code=zip_code,
        kg_co2_week=kg_co2,
        week_number=week,
        year=year,
    )
    session.add(record)
    await session.flush()


async def get_zip_footprints(
    session: AsyncSession,
    zip_code: str,
    week: int,
    year: int,
) -> list[float]:
    """Return all kg_co2_week values for a ZIP in a given week."""
    stmt = select(AnonymizedFootprint.kg_co2_week).where(
        AnonymizedFootprint.zip_code == zip_code,
        AnonymizedFootprint.week_number == week,
        AnonymizedFootprint.year == year,
    )
    result = await session.execute(stmt)
    return [row[0] for row in result.fetchall()]


async def upsert_user_footprint_ref(
    session: AsyncSession,
    user_id: UUID,
    zip_code: str,
    kg: float,
    display_name: str | None = None,
) -> None:
    """Insert or update the user's footprint reference."""
    uid = str(user_id)
    stmt = select(UserFootprintRef).where(UserFootprintRef.user_id == uid)
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    now = datetime.now(tz=ROME_TZ)
    if existing is not None:
        existing.zip_code = zip_code
        existing.last_kg_co2 = kg
        existing.updated_at = now
        if display_name is not None:
            existing.display_name = display_name
    else:
        ref = UserFootprintRef(
            user_id=uid,
            display_name=display_name,
            zip_code=zip_code,
            last_kg_co2=kg,
            updated_at=now,
        )
        session.add(ref)
    await session.flush()


async def get_user_footprint_ref(
    session: AsyncSession,
    user_id: UUID,
) -> UserFootprintRef | None:
    """Get the user's footprint reference, or None."""
    stmt = select(UserFootprintRef).where(UserFootprintRef.user_id == str(user_id))
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_leaderboard(
    session: AsyncSession,
    zip_code: str | None,
    limit: int = 50,
) -> list[dict]:
    """Return users ranked by lowest CO2, optionally filtered by ZIP."""
    stmt = select(
        UserFootprintRef.user_id,
        UserFootprintRef.display_name,
        UserFootprintRef.last_kg_co2,
        UserFootprintRef.zip_code,
    ).order_by(UserFootprintRef.last_kg_co2.asc()).limit(limit)

    if zip_code:
        stmt = stmt.where(UserFootprintRef.zip_code == zip_code)

    result = await session.execute(stmt)
    rows = result.fetchall()
    return [
        {
            "user_id": row[0],
            "display_name": row[1] or "Anonymous",
            "kg_co2_week": round(row[2], 2),
            "zip_code": row[3],
        }
        for row in rows
    ]


async def join_challenge(
    session: AsyncSession,
    challenge_id: str,
    user_id: UUID,
    week: int,
    year: int,
) -> None:
    """Join a challenge (idempotent — skips if already joined)."""
    uid = str(user_id)
    stmt = select(ChallengeParticipant).where(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == uid,
        ChallengeParticipant.week_number == week,
        ChallengeParticipant.year == year,
    )
    result = await session.execute(stmt)
    if result.scalar_one_or_none() is not None:
        return

    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=uid,
        week_number=week,
        year=year,
    )
    session.add(participant)
    await session.flush()


async def get_challenge_participant_count(
    session: AsyncSession,
    challenge_id: str,
    week: int,
    year: int,
) -> int:
    """Count participants for a challenge in a given week."""
    stmt = select(func.count()).select_from(ChallengeParticipant).where(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.week_number == week,
        ChallengeParticipant.year == year,
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def is_user_joined(
    session: AsyncSession,
    challenge_id: str,
    user_id: UUID,
    week: int,
    year: int,
) -> bool:
    """Check if a user has joined a challenge this week."""
    uid = str(user_id)
    stmt = select(func.count()).select_from(ChallengeParticipant).where(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == uid,
        ChallengeParticipant.week_number == week,
        ChallengeParticipant.year == year,
    )
    result = await session.execute(stmt)
    return result.scalar_one() > 0
