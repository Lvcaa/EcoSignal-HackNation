"""Shared fixtures for env-data tests."""

from __future__ import annotations

from typing import AsyncIterator

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Fake Redis
# ---------------------------------------------------------------------------


@pytest.fixture
async def fake_redis() -> AsyncIterator[fakeredis.aioredis.FakeRedis]:
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    yield r
    await r.aclose()


# ---------------------------------------------------------------------------
# ASGI test client (overrides app.state.redis with fake)
# ---------------------------------------------------------------------------


@pytest.fixture
async def client(fake_redis: fakeredis.aioredis.FakeRedis) -> AsyncIterator[AsyncClient]:
    app.state.redis = fake_redis
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Synthetic API response fixtures
# ---------------------------------------------------------------------------

MOCK_OPENAQ_RESPONSE: dict = {
    "results": [
        {
            "id": 12345,
            "name": "Roma Cipro",
            "sensors": [
                {
                    "parameter": {"name": "pm25"},
                    "latest": {"value": 18.5},
                },
                {
                    "parameter": {"name": "pm10"},
                    "latest": {"value": 32.0},
                },
                {
                    "parameter": {"name": "o3"},
                    "latest": {"value": 45.0},
                },
            ],
        }
    ]
}

MOCK_OPENAQ_EMPTY: dict = {"results": []}

MOCK_FORECAST_RESPONSE: dict = {
    "current": {
        "temperature_2m": 22.3,
    }
}

MOCK_ARCHIVE_RESPONSE: dict = {
    "daily": {
        "temperature_2m_mean": [19.5, 20.1, 20.8, 19.9, 20.2, 20.5, 19.8, 20.0, 20.3, 19.7],
    }
}
