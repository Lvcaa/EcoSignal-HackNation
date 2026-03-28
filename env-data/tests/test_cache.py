"""Dedicated unit tests for cache.py — stale fallback, TTL, ZIP activity."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import fakeredis.aioredis

from app.cache import get_active_zips, get_cached, record_zip_activity, set_cached
from app.config import Settings
from app.schemas import DataSource
from app.service import get_env_data

# ---------------------------------------------------------------------------
# get_cached / set_cached round-trip
# ---------------------------------------------------------------------------


class TestGetCachedSetCached:
    async def test_set_then_get_returns_fresh(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        data = {"zip_code": "00100", "value": 42}
        await set_cached(fake_redis, "env:air:00100", data, ttl=3600)

        result = await get_cached(fake_redis, "env:air:00100")

        assert result is not None
        assert result.is_stale is False
        assert result.data["zip_code"] == "00100"
        assert result.data["value"] == 42
        assert "_cached_at" not in result.data

    async def test_primary_expired_stale_present(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        data = {"zip_code": "00100", "value": 42}
        await set_cached(fake_redis, "env:air:00100", data, ttl=3600)
        # Simulate primary key expiry
        await fake_redis.delete("env:air:00100")

        result = await get_cached(fake_redis, "env:air:00100")

        assert result is not None
        assert result.is_stale is True
        assert result.data["zip_code"] == "00100"

    async def test_both_missing_returns_none(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        result = await get_cached(fake_redis, "env:air:00100")
        assert result is None

    async def test_redis_error_returns_none(self) -> None:
        broken_redis = AsyncMock()
        broken_redis.get = AsyncMock(side_effect=ConnectionError("refused"))

        result = await get_cached(broken_redis, "env:air:00100")
        assert result is None

    async def test_cached_at_parsed(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        data = {"zip_code": "00100"}
        await set_cached(fake_redis, "env:air:00100", data, ttl=3600)

        result = await get_cached(fake_redis, "env:air:00100")

        assert result is not None
        assert isinstance(result.cached_at, datetime)
        # Should be close to now
        delta = (datetime.now(UTC) - result.cached_at).total_seconds()
        assert delta < 5


# ---------------------------------------------------------------------------
# set_cached TTL behaviour
# ---------------------------------------------------------------------------


class TestSetCached:
    async def test_primary_key_ttl(self, fake_redis: fakeredis.aioredis.FakeRedis) -> None:
        await set_cached(fake_redis, "env:air:00100", {"v": 1}, ttl=3600)
        ttl = await fake_redis.ttl("env:air:00100")
        assert 0 < ttl <= 3600

    async def test_stale_key_ttl(self, fake_redis: fakeredis.aioredis.FakeRedis) -> None:
        await set_cached(fake_redis, "env:air:00100", {"v": 1}, ttl=3600)
        ttl = await fake_redis.ttl("env:air:00100:stale")
        assert 0 < ttl <= 86400

    async def test_stale_ttl_independent_of_primary(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await set_cached(fake_redis, "env:air:00100", {"v": 1}, ttl=600)
        primary_ttl = await fake_redis.ttl("env:air:00100")
        stale_ttl = await fake_redis.ttl("env:air:00100:stale")
        assert primary_ttl <= 600
        assert stale_ttl > 600  # default stale_ttl=86400

    async def test_custom_stale_ttl(self, fake_redis: fakeredis.aioredis.FakeRedis) -> None:
        await set_cached(fake_redis, "env:air:00100", {"v": 1}, ttl=3600, stale_ttl=7200)
        ttl = await fake_redis.ttl("env:air:00100:stale")
        assert 0 < ttl <= 7200


# ---------------------------------------------------------------------------
# ZIP activity tracking
# ---------------------------------------------------------------------------


class TestZipActivity:
    async def test_record_three_and_get_all(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await record_zip_activity(fake_redis, "00100")
        await record_zip_activity(fake_redis, "20100")
        await record_zip_activity(fake_redis, "40100")

        result = await get_active_zips(fake_redis)
        assert set(result) == {"00100", "20100", "40100"}
        assert len(result) == 3

    async def test_duplicate_appears_once(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await record_zip_activity(fake_redis, "00100")
        await record_zip_activity(fake_redis, "00100")

        result = await get_active_zips(fake_redis)
        assert result == ["00100"]

    async def test_limit_respected(self, fake_redis: fakeredis.aioredis.FakeRedis) -> None:
        for i, z in enumerate(["00100", "20100", "40100", "80100", "90100"]):
            await fake_redis.zadd("ecosignal:active_zips", {z: float(i)})

        result = await get_active_zips(fake_redis, limit=2)
        assert len(result) == 2

    async def test_sorted_by_most_recent(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        await fake_redis.zadd(
            "ecosignal:active_zips", {"00100": 100, "20100": 300, "40100": 200}
        )

        result = await get_active_zips(fake_redis)
        assert result == ["20100", "40100", "00100"]

    async def test_empty_returns_empty_list(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        result = await get_active_zips(fake_redis)
        assert result == []


# ---------------------------------------------------------------------------
# Stale-while-revalidate integration (service + fakeredis)
# ---------------------------------------------------------------------------

_SETTINGS = Settings(openaq_api_key="test-key")  # type: ignore[call-arg]


class TestStaleWhileRevalidate:
    async def test_stale_data_returned_with_background_refresh(
        self, fake_redis: fakeredis.aioredis.FakeRedis
    ) -> None:
        now = datetime.now(UTC)

        air_data = {
            "zip_code": "00100",
            "pm25": 18.5,
            "pm10": 32.0,
            "o3": 45.0,
            "aqi_label": "moderate",
            "fetched_at": now.isoformat(),
            "source": "openaq",
            "is_fallback": False,
            "station_name": "Roma Cipro",
            "station_id": "12345",
            "_cached_at": now.isoformat(),
        }
        climate_data = {
            "zip_code": "00100",
            "current_temp_c": 22.3,
            "anomaly_c": 2.12,
            "anomaly_label": "+2.12\u00b0C above historical average",
            "fetched_at": now.isoformat(),
            "source": "open_meteo",
            "is_fallback": False,
            "_cached_at": now.isoformat(),
        }

        # Seed stale keys only — no primary keys
        await fake_redis.set("env:air:00100:stale", json.dumps(air_data, default=str))
        await fake_redis.set(
            "env:climate:00100:stale", json.dumps(climate_data, default=str)
        )

        with patch("app.service.asyncio.create_task") as mock_create_task:
            result = await get_env_data("00100", fake_redis, _SETTINGS)

        # Returns stale data immediately
        assert result.zip_code == "00100"
        assert result.air_quality.source == DataSource.CACHE
        assert result.air_quality.pm25 == 18.5
        assert result.climate.source == DataSource.CACHE
        assert result.climate.current_temp_c == 22.3

        # Background refresh was scheduled
        mock_create_task.assert_called_once()
