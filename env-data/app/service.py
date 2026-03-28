"""Business logic and orchestration for the env-data service.

Zero imports from ``fastapi`` — this module is pure domain logic.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import Any

import httpx

from app.cache import get_cached, record_zip_activity, set_cached
from app.config import Settings
from app.schemas import (
    AirQualityReading,
    AQILabel,
    ClimateContext,
    DataSource,
    EnvDataResponse,
)
from app.zip_mapping import get_zip_location

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure AQI derivation
# ---------------------------------------------------------------------------


def derive_aqi_label(pm25: float | None, pm10: float | None) -> AQILabel:
    """Derive an AQI label from PM2.5 (preferred) or PM10 using WHO thresholds.

    WHO Global Air Quality Guidelines 2021 — PM2.5 24-hour thresholds:
      good:      < 15 ug/m3
      moderate:  15 .. < 35 ug/m3
      unhealthy: 35 .. < 55 ug/m3
      hazardous: >= 55 ug/m3

    If PM2.5 is None, estimate from PM10: ``pm25_est = pm10 * 0.6``.
    If both are None, return ``moderate`` as a safe default.
    """
    effective_pm25 = pm25
    if effective_pm25 is None:
        if pm10 is not None:
            effective_pm25 = pm10 * 0.6
        else:
            return AQILabel.MODERATE

    if effective_pm25 < 15:
        return AQILabel.GOOD
    if effective_pm25 < 35:
        return AQILabel.MODERATE
    if effective_pm25 < 55:
        return AQILabel.UNHEALTHY
    return AQILabel.HAZARDOUS


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_AIR_KEY = "env:air:{zip_code}"
_CLIMATE_KEY = "env:climate:{zip_code}"


def _fallback_air(zip_code: str) -> AirQualityReading:
    return AirQualityReading(
        zip_code=zip_code,
        aqi_label=AQILabel.MODERATE,
        fetched_at=datetime.now(UTC),
        source=DataSource.FALLBACK,
        is_fallback=True,
    )


def _fallback_climate(zip_code: str) -> ClimateContext:
    return ClimateContext(
        zip_code=zip_code,
        fetched_at=datetime.now(UTC),
        source=DataSource.FALLBACK,
        is_fallback=True,
    )


async def get_env_data(
    zip_code: str,
    redis_client: Any,
    settings: Settings,
) -> EnvDataResponse:
    """Fetch combined environmental data for *zip_code*.

    Raises ``ValueError`` if the ZIP code is not in the mapping.
    """
    location = get_zip_location(zip_code)
    if location is None:
        raise ValueError("ZIP code not supported")

    air_key = _AIR_KEY.format(zip_code=zip_code)
    climate_key = _CLIMATE_KEY.format(zip_code=zip_code)

    # --- check cache concurrently ---
    air_cached, climate_cached = await asyncio.gather(
        get_cached(redis_client, air_key),
        get_cached(redis_client, climate_key),
    )

    air_reading: AirQualityReading | None = None
    climate_ctx: ClimateContext | None = None
    any_stale = False

    if air_cached is not None:
        air_reading = AirQualityReading(**{**air_cached.data, "source": DataSource.CACHE})
        if air_cached.is_stale:
            any_stale = True
    if climate_cached is not None:
        climate_ctx = ClimateContext(**{**climate_cached.data, "source": DataSource.CACHE})
        if climate_cached.is_stale:
            any_stale = True

    if air_reading and climate_ctx:
        if any_stale:
            asyncio.create_task(refresh_env_data(zip_code, redis_client, settings))
        return EnvDataResponse(
            zip_code=zip_code,
            air_quality=air_reading,
            climate=climate_ctx,
            fetched_at=datetime.now(UTC),
        )

    # --- fetch missing data live ---
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        tasks: list[Any] = []
        fetch_air = air_reading is None
        fetch_climate = climate_ctx is None

        if fetch_air:
            tasks.append(_safe_fetch_air(client, location, settings))
        if fetch_climate:
            tasks.append(_safe_fetch_climate(client, location, settings))

        results = await asyncio.gather(*tasks)

        idx = 0
        if fetch_air:
            air_reading = results[idx]
            idx += 1
        if fetch_climate:
            climate_ctx = results[idx]

    # --- cache successful live fetches ---
    assert air_reading is not None
    assert climate_ctx is not None

    cache_tasks = []
    if not air_reading.is_fallback and air_reading.source != DataSource.CACHE:
        cache_tasks.append(
            set_cached(redis_client, air_key, air_reading.model_dump(), settings.cache_ttl_seconds)
        )
    if not climate_ctx.is_fallback and climate_ctx.source != DataSource.CACHE:
        cache_tasks.append(
            set_cached(
                redis_client, climate_key, climate_ctx.model_dump(), settings.cache_ttl_seconds
            )
        )
    if cache_tasks:
        await asyncio.gather(*cache_tasks)

    await record_zip_activity(redis_client, zip_code)

    return EnvDataResponse(
        zip_code=zip_code,
        air_quality=air_reading,
        climate=climate_ctx,
        fetched_at=datetime.now(UTC),
    )


async def refresh_env_data(
    zip_code: str,
    redis_client: Any,
    settings: Settings,
) -> None:
    """Background refresh — fetch live data and update cache. Never raises."""
    try:
        location = get_zip_location(zip_code)
        if location is None:
            return

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            air_reading, climate_ctx = await asyncio.gather(
                _safe_fetch_air(client, location, settings),
                _safe_fetch_climate(client, location, settings),
            )

        air_key = _AIR_KEY.format(zip_code=zip_code)
        climate_key = _CLIMATE_KEY.format(zip_code=zip_code)

        cache_tasks = []
        if not air_reading.is_fallback:
            cache_tasks.append(
                set_cached(
                    redis_client, air_key, air_reading.model_dump(), settings.cache_ttl_seconds
                )
            )
        if not climate_ctx.is_fallback:
            cache_tasks.append(
                set_cached(
                    redis_client, climate_key, climate_ctx.model_dump(), settings.cache_ttl_seconds
                )
            )
        if cache_tasks:
            await asyncio.gather(*cache_tasks)

        await record_zip_activity(redis_client, zip_code)
    except Exception:
        logger.warning("Background refresh failed for zip=%s", zip_code, exc_info=True)


async def _safe_fetch_air(
    client: httpx.AsyncClient,
    location: Any,
    settings: Settings,
) -> AirQualityReading:
    from app.adapters import fetch_air_quality

    try:
        return await fetch_air_quality(client, location, settings)
    except Exception:
        logger.warning("OpenAQ fetch failed for %s", location.zip_code, exc_info=True)
        return _fallback_air(location.zip_code)


async def _safe_fetch_climate(
    client: httpx.AsyncClient,
    location: Any,
    settings: Settings,
) -> ClimateContext:
    from app.adapters import fetch_climate_context

    try:
        return await fetch_climate_context(client, location, settings)
    except Exception:
        logger.warning("Open-Meteo fetch failed for %s", location.zip_code, exc_info=True)
        return _fallback_climate(location.zip_code)
