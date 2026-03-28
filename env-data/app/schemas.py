"""EcoSignal env-data module — Pydantic v2 schemas.

All schemas for the environmental data aggregation service.
No external API imports — pure data definitions only.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AQILabel(StrEnum):
    """Air Quality Index label based on WHO PM2.5 24-hour thresholds.

    Derivation rules (source: WHO Global Air Quality Guidelines, 2021):
      good:       PM2.5 < 15 ug/m3
      moderate:   15 <= PM2.5 < 35 ug/m3
      unhealthy:  35 <= PM2.5 < 55 ug/m3
      hazardous:  PM2.5 >= 55 ug/m3

    If PM2.5 is None:
      - Estimate from PM10 using ratio: estimated_pm25 = pm10 * 0.6
      - If PM10 is also None: default to "moderate"
    """

    GOOD = "good"
    MODERATE = "moderate"
    UNHEALTHY = "unhealthy"
    HAZARDOUS = "hazardous"


class DataSource(StrEnum):
    """Origin of the data returned in a response."""

    OPENAQ = "openaq"
    OPEN_METEO = "open_meteo"
    CACHE = "cache"
    FALLBACK = "fallback"


# ---------------------------------------------------------------------------
# Internal schemas (not exposed via API)
# ---------------------------------------------------------------------------


class ZipLocation(BaseModel):
    """Maps an Italian ZIP (CAP) to geographic coordinates and ARPA region."""

    zip_code: str = Field(description="Italian CAP code (5 digits)")
    city: str
    region: str = Field(description="Italian region name")
    latitude: float
    longitude: float
    arpa_region: str = Field(
        description="ARPA regional agency code, e.g. ARPA_LOMBARDIA"
    )


class OpenAQStation(BaseModel):
    """Nearest OpenAQ monitoring station to a given location."""

    station_id: str
    name: str
    latitude: float
    longitude: float
    distance_km: float = Field(ge=0)


# ---------------------------------------------------------------------------
# Core response schemas
# ---------------------------------------------------------------------------


class AirQualityReading(BaseModel):
    """Air quality snapshot for a ZIP code.

    AQI label derivation (WHO PM2.5 24h thresholds, 2021 guidelines):
      - pm25 < 15           -> good
      - 15 <= pm25 < 35     -> moderate
      - 35 <= pm25 < 55     -> unhealthy
      - pm25 >= 55          -> hazardous

    Fallback when pm25 is None:
      - If pm10 is available: estimated_pm25 = pm10 * 0.6, apply thresholds
      - If both are None: label defaults to "moderate"
    """

    zip_code: str
    station_name: str | None = None
    station_id: str | None = None
    pm25: float | None = Field(default=None, description="PM2.5 in ug/m3")
    pm10: float | None = Field(default=None, description="PM10 in ug/m3")
    o3: float | None = Field(default=None, description="Ozone in ug/m3")
    aqi_label: AQILabel = Field(
        description="Derived from PM2.5 using WHO thresholds"
    )
    fetched_at: datetime
    source: DataSource
    is_fallback: bool = False


class ClimateContext(BaseModel):
    """Temperature anomaly context for a ZIP code.

    anomaly_c = current_temp_c - historical_30yr_avg
    Positive values mean warmer than average.
    """

    zip_code: str
    current_temp_c: float | None = None
    anomaly_c: float | None = Field(
        default=None,
        description="Current temp minus 30-year historical average (positive = warmer)",
    )
    anomaly_label: str | None = Field(
        default=None,
        description='Human-readable label, e.g. "+2.1C above historical average"',
    )
    fetched_at: datetime
    source: DataSource
    is_fallback: bool = False


class EnvDataResponse(BaseModel):
    """Combined environmental data response returned to api-gateway."""

    zip_code: str
    air_quality: AirQualityReading
    climate: ClimateContext
    fetched_at: datetime
