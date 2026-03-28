"""HTTP adapters for OpenAQ and Open-Meteo APIs.

Zero imports from ``fastapi``. All external HTTP goes through the injected
``httpx.AsyncClient`` — never create a client inside these functions.
"""

from __future__ import annotations

import asyncio
import logging
import statistics
from datetime import UTC, datetime, timedelta

import httpx

from app.config import Settings
from app.schemas import (
    AirQualityReading,
    AQILabel,
    ClimateContext,
    DataSource,
    ZipLocation,
)
from app.service import derive_aqi_label

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# OpenAQ adapter
# ---------------------------------------------------------------------------


async def fetch_air_quality(
    client: httpx.AsyncClient,
    location: ZipLocation,
    settings: Settings,
) -> AirQualityReading:
    """Fetch the nearest air-quality station from OpenAQ v3.

    Returns a fallback ``AirQualityReading`` (``is_fallback=True``) when no
    station is found within the search radius. Raises on HTTP / timeout errors
    so the caller can decide on fallback strategy.
    """
    url = f"{settings.openaq_base_url}/locations"
    params: dict[str, str | int] = {
        "coordinates": f"{location.latitude},{location.longitude}",
        "radius": 50000,
        "limit": 1,
        "order_by": "distance",
    }
    headers = {"X-API-Key": settings.openaq_api_key}

    resp = await client.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results", [])
    if not results:
        return AirQualityReading(
            zip_code=location.zip_code,
            aqi_label=AQILabel.MODERATE,
            fetched_at=datetime.now(UTC),
            source=DataSource.OPENAQ,
            is_fallback=True,
        )

    station = results[0]
    station_name = station.get("name")
    station_id = str(station.get("id", ""))

    # Extract pollutant values from latest measurements
    pm25: float | None = None
    pm10: float | None = None
    o3: float | None = None

    sensors = station.get("sensors", [])
    for sensor in sensors:
        param = sensor.get("parameter", {})
        param_name = param.get("name", "").lower() if isinstance(param, dict) else ""
        latest = sensor.get("latest", {})
        value = latest.get("value")
        if value is None:
            continue
        if "pm25" in param_name or "pm2.5" in param_name:
            pm25 = float(value)
        elif "pm10" in param_name:
            pm10 = float(value)
        elif "o3" in param_name or "ozone" in param_name:
            o3 = float(value)

    aqi_label = derive_aqi_label(pm25, pm10)

    return AirQualityReading(
        zip_code=location.zip_code,
        station_name=station_name,
        station_id=station_id,
        pm25=pm25,
        pm10=pm10,
        o3=o3,
        aqi_label=aqi_label,
        fetched_at=datetime.now(UTC),
        source=DataSource.OPENAQ,
    )


# ---------------------------------------------------------------------------
# Open-Meteo adapter
# ---------------------------------------------------------------------------


async def fetch_climate_context(
    client: httpx.AsyncClient,
    location: ZipLocation,
    settings: Settings,
) -> ClimateContext:
    """Fetch current temperature and historical anomaly from Open-Meteo.

    Makes two concurrent requests (forecast + archive) and computes the
    temperature anomaly. Raises on any failure.
    """
    now = datetime.now(UTC)

    # Current temperature
    forecast_url = f"{settings.open_meteo_base_url}/forecast"
    forecast_params: dict[str, str | float] = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "current": "temperature_2m",
    }

    # Historical average: 10-year window, same month
    month_start = now.replace(day=1)
    if now.month == 12:
        month_end = now.replace(year=now.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end = now.replace(month=now.month + 1, day=1) - timedelta(days=1)

    hist_start = month_start.replace(year=now.year - 10)
    hist_end = month_end.replace(year=now.year - 1)

    archive_url = f"{settings.open_meteo_base_url}/archive"
    archive_params: dict[str, str | float] = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "start_date": hist_start.strftime("%Y-%m-%d"),
        "end_date": hist_end.strftime("%Y-%m-%d"),
        "daily": "temperature_2m_mean",
    }

    forecast_resp, archive_resp = await asyncio.gather(
        client.get(forecast_url, params=forecast_params),
        client.get(archive_url, params=archive_params),
    )
    forecast_resp.raise_for_status()
    archive_resp.raise_for_status()

    forecast_data = forecast_resp.json()
    archive_data = archive_resp.json()

    current_temp = forecast_data["current"]["temperature_2m"]

    daily_temps = archive_data.get("daily", {}).get("temperature_2m_mean", [])
    valid_temps = [t for t in daily_temps if t is not None]

    if not valid_temps:
        return ClimateContext(
            zip_code=location.zip_code,
            current_temp_c=current_temp,
            fetched_at=datetime.now(UTC),
            source=DataSource.OPEN_METEO,
        )

    historical_avg = statistics.mean(valid_temps)
    anomaly_c = round(current_temp - historical_avg, 2)

    if anomaly_c >= 0:
        anomaly_label = f"+{anomaly_c}\u00b0C above historical average"
    else:
        anomaly_label = f"{anomaly_c}\u00b0C below historical average"

    return ClimateContext(
        zip_code=location.zip_code,
        current_temp_c=current_temp,
        anomaly_c=anomaly_c,
        anomaly_label=anomaly_label,
        fetched_at=datetime.now(UTC),
        source=DataSource.OPEN_METEO,
    )
