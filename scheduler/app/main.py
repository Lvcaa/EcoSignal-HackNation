"""EcoSignal Scheduler — FastAPI application with APScheduler 4.x."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from apscheduler import AsyncScheduler, ConflictPolicy
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.jobs import prefetch_active_zips, weekly_digest_log

settings = get_settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

scheduler: AsyncScheduler | None = None

JOB_REGISTRY: dict[str, Any] = {
    "prefetch_active_zips": prefetch_active_zips,
    "weekly_digest_log": weekly_digest_log,
}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    global scheduler  # noqa: PLW0603
    scheduler = AsyncScheduler()

    async with scheduler:
        await scheduler.add_schedule(
            prefetch_active_zips,
            CronTrigger(hour=7, minute=0, timezone=settings.job_timezone),
            id="prefetch_active_zips",
            conflict_policy=ConflictPolicy.replace,
        )
        await scheduler.add_schedule(
            weekly_digest_log,
            CronTrigger(
                day_of_week="mon", hour=6, minute=0, timezone=settings.job_timezone
            ),
            id="weekly_digest_log",
            conflict_policy=ConflictPolicy.replace,
        )
        logger.info("Scheduler started with timezone=%s", settings.job_timezone)
        await scheduler.start_in_background()
        yield

    scheduler = None


app = FastAPI(title="EcoSignal Scheduler", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, Any]:
    jobs: list[dict[str, str]] = []
    if scheduler is not None:
        schedules = await scheduler.get_schedules()
        jobs = [
            {
                "id": s.id,
                "next_fire_time": str(s.next_fire_time) if s.next_fire_time else "N/A",
            }
            for s in schedules
        ]
    return {"status": "ok", "version": "1.0.0", "jobs": jobs}


@app.get("/health/trigger/{job_id}")
async def trigger_job(job_id: str) -> dict[str, str]:
    func = JOB_REGISTRY.get(job_id)
    if func is None:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}")
    logger.info("Manually triggering job: %s", job_id)
    await func()
    return {"triggered": job_id, "status": "fired"}
