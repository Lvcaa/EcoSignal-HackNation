"""TASK-20: Deep cache hit/miss integration tests.

Tests the interaction between cache.py and service.py under every
realistic cache state. All tests use fakeredis + pytest-httpx — zero
real Redis or HTTP connections.
"""

from __future__ import annotations

import asyncio
import json
import re
import time
from datetime import UTC, datetime
from unittest.mock import patch

import fakeredis.aioredis
import httpx
from pytest_httpx import HTTPXMock

from app.cache import set_cached
from app.config import Settings
from app.schemas import DataSource
from app.service import get_env_data

_SETTINGS = Settings(openaq_api_key="test-key")  # type: ignore[call-arg]

# ---------------------------------------------------------------------------
# Helpers: seed data + mock HTTP responses
# ---------------------------------------------------------------------------

_NOW_ISO = datetime.now(UTC).isoformat()

AIR_DATA: dict = {
    "zip_code": "00100",
    "pm25": 18.5,
    "pm10": 32.0,
    "o3": 45.0,
    "aqi_label": "moderate",
    "fetched_at": _NOW_ISO,
    "source": "openaq",
    "is_fallback": False,
    "station_name": "Roma Cipro",
    "station_id": "12345",
}

CLIMATE_DATA: dict = {
    "zip_code": "00100",
    "current_temp_c": 22.3,
    "anomaly_c": 2.12,
    "anomaly_label": "+2.12\u00b0C above historical average",
    "fetched_at": _NOW_ISO,
    "source": "open_meteo",
    "is_fallback": False,
}

OPENAQ_RESPONSE: dict = {
    "results": [
        {
            "id": 12345,
            "name": "Roma Cipro",
            "sensors": [
                {"parameter": {"name": "pm25"}, "latest": {"value": 18.5}},
                {"parameter": {"name": "pm10"}, "latest": {"value": 32.0}},
                {"parameter": {"name": "o3"}, "latest": {"value": 45.0}},
            ],
        }
    ]
}

FORECAST_RESPONSE: dict = {"current": {"temperature_2m": 22.3}}

ARCHIVE_RESPONSE: dict = {
    "daily": {"temperature_2m_mean": [19.5, 20.1, 20.8, 19.9, 20.2, 20.5, 19.8]}
}


async def _seed_fresh(
    redis: fakeredis.aioredis.FakeRedis,
    air: bool = True,
    climate: bool = True,
) -> None:
    """Seed both primary and stale keys (fresh state)."""
    stamped_air = {**AIR_DATA, "_cached_at": _NOW_ISO}
    stamped_climate = {**CLIMATE_DATA, "_cached_at": _NOW_ISO}
    if air:
        await redis.set("env:air:00100", json.dumps(stamped_air, default=str), ex=3600)
        await redis.set(
            "env:air:00100:stale", json.dumps(stamped_air, default=str), ex=86400
        )
    if climate:
        await redis.set(
            "env:climate:00100", json.dumps(stamped_climate, default=str), ex=3600
        )
        await redis.set(
            "env:climate:00100:stale", json.dumps(stamped_climate, default=str), ex=86400
        )


async def _seed_stale(
    redis: fakeredis.aioredis.FakeRedis,
    air: bool = True,
    climate: bool = True,
) -> None:
    """Seed stale keys only (primary expired)."""
    stamped_air = {**AIR_DATA, "_cached_at": _NOW_ISO}
    stamped_climate = {**CLIMATE_DATA, "_cached_at": _NOW_ISO}
    if air:
        await redis.set(
            "env:air:00100:stale", json.dumps(stamped_air, default=str), ex=86400
        )
    if climate:
        await redis.set(
            "env:climate:00100:stale", json.dumps(stamped_climate, default=str), ex=86400
        )


def _register_openaq(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=re.compile(r".*/locations.*"), json=OPENAQ_RESPONSE)


def _register_meteo(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=re.compile(r".*/forecast.*"), json=FORECAST_RESPONSE)
    httpx_mock.add_response(url=re.compile(r".*/archive.*"), json=ARCHIVE_RESPONSE)


# ===========================================================================
# Cache state matrix
# ===========================================================================


class TestCacheStateA_BothFresh:
    """State A — both air and climate primary keys present (fresh)."""

    async def test_zero_http_calls(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_fresh(fake_redis)
        await get_env_data("00100", fake_redis, _SETTINGS)
        assert len(httpx_mock.get_requests()) == 0

    async def test_source_is_cache(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_fresh(fake_redis)
        result = await get_env_data("00100", fake_redis, _SETTINGS)
        assert result.air_quality.source == DataSource.CACHE
        assert result.climate.source == DataSource.CACHE

    async def test_is_fallback_false(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_fresh(fake_redis)
        result = await get_env_data("00100", fake_redis, _SETTINGS)
        assert result.air_quality.is_fallback is False
        assert result.climate.is_fallback is False


class TestCacheStateB_BothStale:
    """State B — both primary keys expired, only stale keys present."""

    async def test_zero_http_calls(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis)
        with patch("app.service.asyncio.create_task"):
            await get_env_data("00100", fake_redis, _SETTINGS)
        assert len(httpx_mock.get_requests()) == 0

    async def test_background_refresh_fired(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis)
        with patch("app.service.asyncio.create_task") as mock_ct:
            await get_env_data("00100", fake_redis, _SETTINGS)
        mock_ct.assert_called_once()

    async def test_stale_data_values_returned(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis)
        with patch("app.service.asyncio.create_task"):
            result = await get_env_data("00100", fake_redis, _SETTINGS)
        assert result.air_quality.pm25 == 18.5
        assert result.climate.current_temp_c == 22.3


class TestCacheStateC_AirFreshClimateStale:
    """State C — air fresh (primary present), climate stale only."""

    async def test_zero_http_calls(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_fresh(fake_redis, air=True, climate=False)
        await _seed_stale(fake_redis, air=False, climate=True)
        with patch("app.service.asyncio.create_task"):
            await get_env_data("00100", fake_redis, _SETTINGS)
        assert len(httpx_mock.get_requests()) == 0

    async def test_background_refresh_for_climate(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_fresh(fake_redis, air=True, climate=False)
        await _seed_stale(fake_redis, air=False, climate=True)
        with patch("app.service.asyncio.create_task") as mock_ct:
            await get_env_data("00100", fake_redis, _SETTINGS)
        mock_ct.assert_called_once()


class TestCacheStateD_AirStaleClimateMissing:
    """State D — air stale, climate entirely missing."""

    async def test_one_http_call_group(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis, air=True, climate=False)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        # Only Open-Meteo calls (forecast + archive), no OpenAQ
        urls = [str(r.url) for r in httpx_mock.get_requests()]
        assert any("forecast" in u for u in urls)
        assert any("archive" in u for u in urls)
        assert not any("locations" in u for u in urls)

    async def test_air_from_stale_cache(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis, air=True, climate=False)
        _register_meteo(httpx_mock)

        result = await get_env_data("00100", fake_redis, _SETTINGS)
        assert result.air_quality.source == DataSource.CACHE
        assert result.air_quality.pm25 == 18.5

    async def test_climate_from_live_fetch(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        await _seed_stale(fake_redis, air=True, climate=False)
        _register_meteo(httpx_mock)

        result = await get_env_data("00100", fake_redis, _SETTINGS)
        assert result.climate.source != DataSource.CACHE
        assert result.climate.current_temp_c == 22.3


class TestCacheStateE_BothMissing:
    """State E — cold start, nothing in cache."""

    async def test_two_http_call_groups(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        urls = [str(r.url) for r in httpx_mock.get_requests()]
        assert any("locations" in u for u in urls)
        assert any("forecast" in u for u in urls)
        assert any("archive" in u for u in urls)

    async def test_primary_and_stale_keys_created(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        assert await fake_redis.exists("env:air:00100") == 1
        assert await fake_redis.exists("env:air:00100:stale") == 1
        assert await fake_redis.exists("env:climate:00100") == 1
        assert await fake_redis.exists("env:climate:00100:stale") == 1

    async def test_zip_activity_recorded(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        members = await fake_redis.zrange("ecosignal:active_zips", 0, -1)
        assert "00100" in members


# ===========================================================================
# TTL verification
# ===========================================================================


class TestTTLVerification:
    async def test_primary_key_ttl_range(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        ttl = await fake_redis.ttl("env:air:00100")
        assert 3500 <= ttl <= 3600

    async def test_stale_key_ttl_range(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("00100", fake_redis, _SETTINGS)

        ttl = await fake_redis.ttl("env:air:00100:stale")
        assert 86000 <= ttl <= 86400

    async def test_custom_stale_ttl(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await set_cached(
            fake_redis, "env:air:00100", {"v": 1}, ttl=3600, stale_ttl=7200
        )
        ttl = await fake_redis.ttl("env:air:00100:stale")
        assert 0 < ttl <= 7200

    async def test_primary_disappears_stale_survives(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await set_cached(fake_redis, "env:air:00100", {"v": 1}, ttl=3600)

        # Simulate primary expiry
        await fake_redis.delete("env:air:00100")

        assert await fake_redis.exists("env:air:00100") == 0
        assert await fake_redis.exists("env:air:00100:stale") == 1


# ===========================================================================
# Concurrency
# ===========================================================================


class TestConcurrency:
    async def test_parallel_fetch_faster_than_sequential(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        """OpenAQ ~200ms, Open-Meteo ~100ms — total should be < 350ms."""

        async def slow_openaq(request: httpx.Request) -> httpx.Response:
            await asyncio.sleep(0.2)
            return httpx.Response(200, json=OPENAQ_RESPONSE)

        async def slow_meteo_forecast(request: httpx.Request) -> httpx.Response:
            await asyncio.sleep(0.1)
            return httpx.Response(200, json=FORECAST_RESPONSE)

        async def slow_meteo_archive(request: httpx.Request) -> httpx.Response:
            await asyncio.sleep(0.1)
            return httpx.Response(200, json=ARCHIVE_RESPONSE)

        httpx_mock.add_callback(slow_openaq, url=re.compile(r".*/locations.*"))
        httpx_mock.add_callback(slow_meteo_forecast, url=re.compile(r".*/forecast.*"))
        httpx_mock.add_callback(slow_meteo_archive, url=re.compile(r".*/archive.*"))

        start = time.monotonic()
        await get_env_data("00100", fake_redis, _SETTINGS)
        elapsed = time.monotonic() - start

        assert elapsed < 0.35

    async def test_openaq_timeout_climate_ok(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(
            httpx.TimeoutException("openaq timeout"),
            url=re.compile(r".*/locations.*"),
        )
        _register_meteo(httpx_mock)

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.air_quality.is_fallback is True
        assert result.climate.is_fallback is False

    async def test_both_timeout_returns_200(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        httpx_mock.add_exception(
            httpx.TimeoutException("openaq timeout"),
            url=re.compile(r".*/locations.*"),
        )
        httpx_mock.add_exception(
            httpx.TimeoutException("meteo forecast timeout"),
            url=re.compile(r".*/forecast.*"),
        )
        httpx_mock.add_exception(
            httpx.TimeoutException("meteo archive timeout"),
            url=re.compile(r".*/archive.*"),
        )

        result = await get_env_data("00100", fake_redis, _SETTINGS)

        assert result.air_quality.is_fallback is True
        assert result.climate.is_fallback is True
        # Still returns a valid response (not an exception)
        assert result.zip_code == "00100"


# ===========================================================================
# Cache key correctness
# ===========================================================================


class TestCacheKeyCorrectness:
    async def test_air_key_format(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("20100", fake_redis, _SETTINGS)

        assert await fake_redis.exists("env:air:20100") == 1

    async def test_climate_key_format(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("20100", fake_redis, _SETTINGS)

        assert await fake_redis.exists("env:climate:20100") == 1

    async def test_stale_key_format(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("20100", fake_redis, _SETTINGS)

        assert await fake_redis.exists("env:air:20100:stale") == 1
        assert await fake_redis.exists("env:climate:20100:stale") == 1

    async def test_active_zips_key(
        self, fake_redis: fakeredis.aioredis.FakeRedis, httpx_mock: HTTPXMock
    ) -> None:
        _register_openaq(httpx_mock)
        _register_meteo(httpx_mock)

        await get_env_data("20100", fake_redis, _SETTINGS)

        assert await fake_redis.exists("ecosignal:active_zips") == 1
