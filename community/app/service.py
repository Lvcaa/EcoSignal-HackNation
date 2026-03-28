"""Pure business logic for community service. No FastAPI imports, no DB calls."""

from __future__ import annotations

from typing import Any

from app.schemas import NeighborhoodStats


def compute_neighborhood_stats(
    zip_code: str,
    city: str | None,
    all_footprints: list[float],
    user_kg: float | None,
) -> NeighborhoodStats:
    """Compute aggregated neighborhood statistics for a ZIP code."""
    count = len(all_footprints)
    avg = round(sum(all_footprints) / count, 2) if count > 0 else 0.0

    rank_pct: float | None = None
    better_than_pct: float | None = None

    if user_kg is not None and count > 0:
        rank_pct = round(len([x for x in all_footprints if x <= user_kg]) / count, 2)
        better_than_pct = round(1.0 - rank_pct, 2)

    return NeighborhoodStats(
        zip_code=zip_code,
        city=city,
        avg_kg_co2_week=avg,
        participant_count=count,
        your_kg_co2_week=round(user_kg, 2) if user_kg is not None else None,
        your_rank_pct=rank_pct,
        better_than_pct=better_than_pct,
    )


def get_active_challenge(
    challenges: list[dict[str, Any]],
    week_number: int,
) -> dict[str, Any]:
    """Return the active challenge based on ISO week number (round-robin)."""
    return challenges[week_number % len(challenges)]


def compute_progress_pct(participant_count: int, target: int) -> float:
    """Compute challenge progress as a fraction of target."""
    return round(min(participant_count / target, 1.0), 4)
