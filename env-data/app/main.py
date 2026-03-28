"""EcoSignal Env Data Service — FastAPI application."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, Query

from app.config import Settings
from app.schemas import AirQualityReading, ClimateContext, EnvDataResponse
from app.service import get_env_data

settings = Settings()  # type: ignore[call-arg]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    yield
    await app.state.redis.aclose()


app = FastAPI(title="EcoSignal Env Data Service", lifespan=lifespan)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Env data endpoints
# ---------------------------------------------------------------------------


async def _get_data(zip_code: str) -> EnvDataResponse:
    """Shared helper: resolve ZIP and return combined env data."""
    try:
        return await get_env_data(zip_code, app.state.redis, settings)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/api/v1/env/combined", response_model=EnvDataResponse)
async def combined(zip_code: str = Query(...)) -> Any:
    return await _get_data(zip_code)


@app.get("/api/v1/env/air-quality", response_model=AirQualityReading)
async def air_quality(zip_code: str = Query(...)) -> Any:
    data = await _get_data(zip_code)
    return data.air_quality


@app.get("/api/v1/env/climate-context", response_model=ClimateContext)
async def climate_context(zip_code: str = Query(...)) -> Any:
    data = await _get_data(zip_code)
    return data.climate
