"""Redis cache helpers for env-data service.

Thin async wrappers around redis.asyncio with stale-while-revalidate
support. Never raise on errors — log a warning and return None / silently
skip the write.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class CacheResult(BaseModel):
    """Wrapper returned by :func:`get_cached`."""

    data: dict[str, Any]
    is_stale: bool
    cached_at: datetime


async def get_cached(redis_client: Any, key: str) -> CacheResult | None:
    """Return cached value for *key*, preferring fresh over stale.

    Checks the primary key first; if absent, falls back to the companion
    ``{key}:stale`` key.  Returns ``None`` when both are missing or on
    any Redis error.
    """
    try:
        raw = await redis_client.get(key)
        if raw is not None:
            payload: dict[str, Any] = json.loads(raw)
            cached_at_str = payload.pop("_cached_at", None)
            cached_at = (
                datetime.fromisoformat(cached_at_str)
                if cached_at_str
                else datetime.now(UTC)
            )
            return CacheResult(data=payload, is_stale=False, cached_at=cached_at)

        stale_raw = await redis_client.get(f"{key}:stale")
        if stale_raw is not None:
            payload = json.loads(stale_raw)
            cached_at_str = payload.pop("_cached_at", None)
            cached_at = (
                datetime.fromisoformat(cached_at_str)
                if cached_at_str
                else datetime.now(UTC)
            )
            return CacheResult(data=payload, is_stale=True, cached_at=cached_at)

        return None
    except Exception:
        logger.warning("Redis GET error for key=%s", key, exc_info=True)
        return None


async def set_cached(
    redis_client: Any,
    key: str,
    value: dict[str, Any],
    ttl: int,
    stale_ttl: int = 86400,
) -> None:
    """Store *value* under *key* (primary TTL) and ``{key}:stale`` (stale TTL).

    A ``_cached_at`` ISO timestamp is injected into the stored payload so
    that :func:`get_cached` can populate :pyattr:`CacheResult.cached_at`.
    """
    try:
        stamped = {**value, "_cached_at": datetime.now(UTC).isoformat()}
        payload = json.dumps(stamped, default=str)
        await redis_client.set(key, payload, ex=ttl)
        await redis_client.set(f"{key}:stale", payload, ex=stale_ttl)
    except Exception:
        logger.warning("Redis SET error for key=%s", key, exc_info=True)


# ---------------------------------------------------------------------------
# ZIP activity tracking
# ---------------------------------------------------------------------------


async def record_zip_activity(redis_client: Any, zip_code: str) -> None:
    """Record a ZIP lookup in the ``ecosignal:active_zips`` sorted set.

    The score is the current Unix timestamp so that :func:`get_active_zips`
    can return ZIPs ordered by most-recent activity.
    """
    try:
        await redis_client.zadd("ecosignal:active_zips", {zip_code: time.time()})
    except Exception:
        logger.warning("Redis ZADD error for zip=%s", zip_code, exc_info=True)


async def get_active_zips(redis_client: Any, limit: int = 20) -> list[str]:
    """Return up to *limit* ZIP codes sorted by most recent activity."""
    try:
        result: list[str] = await redis_client.zrevrange(
            "ecosignal:active_zips", 0, limit - 1
        )
        return result
    except Exception:
        logger.warning("Redis ZREVRANGE error", exc_info=True)
        return []
