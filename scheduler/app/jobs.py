"""EcoSignal Scheduler — background job definitions.

All jobs are async, fire-and-forget. Each is wrapped in a top-level
try/except so that failures are logged but never crash the scheduler.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def prefetch_active_zips() -> None:
    """Daily job: prefetch env data for the most active ZIP codes."""
    try:
        settings = get_settings()
        start = time.monotonic()

        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Fetch active ZIPs from env-data service
            resp = await client.get(
                f"{settings.env_data_service_url}/api/v1/env/active-zips",
                params={"limit": settings.prefetch_zip_limit},
            )
            resp.raise_for_status()
            zips: list[str] = resp.json()["zips"]

            if not zips:
                logger.info("prefetch_active_zips: no active ZIPs found, skipping")
                return

            # 2. Prefetch combined env data for each ZIP concurrently
            tasks = [
                client.get(
                    f"{settings.env_data_service_url}/api/v1/env/combined",
                    params={"zip_code": zip_code},
                )
                for zip_code in zips
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            succeeded = sum(1 for r in results if not isinstance(r, BaseException))
            failed = len(results) - succeeded

        elapsed = time.monotonic() - start
        logger.info(
            "prefetch_active_zips: done — %d/%d ZIPs prefetched (%d failed) in %.2fs",
            succeeded,
            len(zips),
            failed,
            elapsed,
        )
    except Exception:
        logger.exception("prefetch_active_zips: job failed")


async def weekly_digest_log() -> None:
    """Weekly job: log a digest summary of system activity."""
    try:
        settings = get_settings()
        now = datetime.now(UTC)
        week_number = now.isocalendar()[1]

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{settings.env_data_service_url}/api/v1/env/active-zips",
                params={"limit": 100},
            )
            resp.raise_for_status()
            zips: list[str] = resp.json()["zips"]

        top_10 = zips[:10]
        logger.info(
            "weekly_digest: week=%d | active_zips=%d | top_10=%s",
            week_number,
            len(zips),
            ", ".join(top_10) if top_10 else "(none)",
        )
    except Exception:
        logger.exception("weekly_digest_log: job failed")
