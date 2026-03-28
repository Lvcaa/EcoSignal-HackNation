"""Unit tests for service.py — AQI derivation and orchestration."""

from __future__ import annotations

import json
import re

import fakeredis.aioredis
import pytest
from pytest_httpx import HTTPXMock

from app.config import Settings
from app.schemas import AQILabel, DataSource
from app.service import derive_aqi_label, get_env_data
from tests.conftest import (
    MOCK_ARCHIVE_RESPONSE,
    MOCK_FORECAST_RESPONSE,
    MOCK_OPENAQ_RESPONSE,
)

# ---------------------------------------------------------------------------
# derive_aqi_label
# ---------------------------------------------------------------------------


class TestDeriveAqiLabel:
    def test_good(self) -> None:
        assert derive_aqi_label(10, None) == AQILabel.GOOD

    def test_moderate(self) -> None:
        assert derive_aqi_label(20, None) == AQILabel.MODERATE

    def test_unhealthy(self) -> None:
        assert derive_aqi_label(40, None) == AQILabel.UNHEALTHY

    def test_hazardous(self) -> None:
        assert derive_aqi_label(60, None) == AQILabel.HAZARDOUS

    def test_pm25_none_pm10_present(self) -> None:
        # pm10=40 → estimated pm25 = 40 * 0.6 = 24 → moderate
        assert derive_aqi_label(None, 40) == AQILabel.MODERATE

    def test_both_none(self) -> None:
        assert derive_aqi_label(None, None) == AQILabel.MODERATE

    def test_boundary_good_moderate(self) -> None:
        assert derive_aqi_label(14.9, None) == AQILabel.GOOD
        assert derive_aqi_label(15.0, None) == AQILabel.MODERATE

    def test_boundary_moderate_unhealthy(self) -> None:
        assert derive_aqi_label(34.9, None) == AQILabel.MODERATE
        assert derive_aqi_label(35.0, None) == AQILabel.UNHEALTHY

    def test_boundary_unhealthy_hazardous(self) -> None:
        assert derive_aqi_label(54.9, None) == AQILabel.UNHEALTHY
        assert derive_aqi_label(55.0, None) == AQILabel.HAZARDOUS


# ---------------------------------------------------------------------------
# get_env_data orchestration
# ---------------------------------------------------------------------------

_SETTINGS = Settings(openaq_api_key="test-key")  # type: ignore[call-arg]


def _register_openaq(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(r".*/locations.*"),
        json=MOCK_OPENAQ_RESPONSE,
    )


def _register_meteo(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        url=re.compile(r".*/forecast.*"),
        json=MOCK_FORECAST_RESPONSE,
    )
    httpx_mock.add_response(
        url=re.compile(r".*/archive.*"),
        json=MOCK_ARCHIVE_RESPONSE,
    )


class TestGetEnvData:
    async def test_cache_miss_fetches_live(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.zip_code == "00100"
        assert result.air_quality.pm25 == 18.5
        assert result.air_quality.source == DataSource.OPENAQ
        assert result.climate.current_temp_c == 22.3
        assert result.climate.source == DataSource.OPEN_METEO

        # Verify data was cached
        air_cached = await fake_redis.get("env:air:00100")
        assert air_cached is not None
        climate_cached = await fake_redis.get("env:climate:00100")
        assert climate_cached is not None

    async def test_cache_hit(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        # Pre-populate cache
        from datetime import UTC, datetime

        air_data = {
            "zip_code": "00100",
            "pm25": 18.5,
            "pm10": 32.0,
            "o3": 45.0,
            "aqi_label": "moderate",
            "fetched_at": datetime.now(UTC).isoformat(),
            "source": "openaq",
            "is_fallback": False,
            "station_name": "Roma Cipro",
            "station_id": "12345",
        }
        climate_data = {
            "zip_code": "00100",
            "current_temp_c": 22.3,
            "anomaly_c": 2.12,
            "anomaly_label": "+2.12\u00b0C above historical average",
            "fetched_at": datetime.now(UTC).isoformat(),
            "source": "open_meteo",
            "is_fallback": False,
        }
        await fake_redis.set("env:air:00100", json.dumps(air_data))
        await fake_redis.set("env:climate:00100", json.dumps(climate_data))

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.air_quality.source == DataSource.CACHE
        assert result.climate.source == DataSource.CACHE
        # No HTTP calls should have been made
        assert len(httpx_mock.get_requests()) == 0

    async def test_openaq_failure_returns_fallback(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=re.compile(r".*/locations.*"), status_code=500)
        _register_meteo(httpx_mock)

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.air_quality.is_fallback is True
        assert result.air_quality.source == DataSource.FALLBACK
        assert result.climate.is_fallback is False

    async def test_open_meteo_failure_returns_fallback(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        httpx_mock.add_response(url=re.compile(r".*/forecast.*"), status_code=500)
        httpx_mock.add_response(url=re.compile(r".*/archive.*"), status_code=500)

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.climate.is_fallback is True
        assert result.climate.source == DataSource.FALLBACK
        assert result.air_quality.is_fallback is False

    async def test_both_fail(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_response(url=re.compile(r".*/locations.*"), status_code=500)
        httpx_mock.add_response(url=re.compile(r".*/forecast.*"), status_code=500)
        httpx_mock.add_response(url=re.compile(r".*/archive.*"), status_code=500)

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.air_quality.is_fallback is True
        assert result.climate.is_fallback is True

    async def test_unknown_zip_raises(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        with pytest.raises(ValueError, match="ZIP code not supported"):
            await get_env_data("99999", fake_redis, _SETTINGS)
