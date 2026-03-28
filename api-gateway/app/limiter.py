from __future__ import annotations

import logging

import redis as redis_lib
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_limiter() -> Limiter:
    """Build a rate limiter, falling back to in-memory storage if Redis is unavailable."""
    settings = get_settings()
    try:
        r = redis_lib.from_url(settings.redis_url, socket_connect_timeout=2)
        r.ping()
        logger.info("Rate limiter connected to Redis at %s", settings.redis_url)
        return Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
            storage_uri=settings.redis_url,
            in_memory_fallback_enabled=True,
        )
    except Exception:
        logger.warning(
            "Redis unavailable at %s — falling back to in-memory rate limiting",
            settings.redis_url,
        )
        return Limiter(
            key_func=get_remote_address,
            default_limits=["100/minute"],
        )


limiter = _build_limiter()


def get_limiter() -> Limiter:
    return limiter
