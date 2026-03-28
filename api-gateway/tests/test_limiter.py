from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from limits.storage import MemoryStorage

from app.auth import create_access_token
from app.config import Settings, get_settings
from app.limiter import limiter
from app.main import app

TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


def _test_settings() -> Settings:
    return Settings(
        secret_key="test-secret-key",
        algorithm="HS256",
        access_token_expire_minutes=60,
        user_profile_service_url="http://mock-user-profile:8000",
        footprint_service_url="http://mock-footprint:8000",
        env_data_service_url="http://mock-env-data:8000",
        ai_narrative_service_url="http://mock-ai-narrative:8000",
        actions_service_url="http://mock-actions:8000",
        community_service_url="http://mock-community:8000",
        redis_url="redis://localhost:6379/1",
        log_level="DEBUG",
    )


@pytest.fixture(autouse=True)
def _reset_limiter() -> None:
    """Reset limiter to fresh in-memory storage before each test."""
    fresh_storage = MemoryStorage()
    limiter._storage = fresh_storage
    limiter._limiter.storage = fresh_storage


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_settings] = _test_settings
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def valid_token() -> str:
    return create_access_token({"sub": TEST_USER_ID})


# ── Test: Global rate limit ─────────────────────────────────


class TestGlobalRateLimit:
    async def test_101st_request_returns_429(self, client: AsyncClient) -> None:
        for i in range(100):
            resp = await client.get("/health")
            assert resp.status_code == 200, f"Request {i + 1} failed unexpectedly"

        resp = await client.get("/health")
        assert resp.status_code == 429


# ── Test: Per-route limit (narrative 5/minute) ──────────────


class TestNarrativeRateLimit:
    @patch("app.router._proxy", new_callable=AsyncMock, return_value={"headline": "test"})
    async def test_6th_narrative_request_returns_429(
        self,
        mock_proxy: AsyncMock,
        client: AsyncClient,
        valid_token: str,
    ) -> None:
        headers = {"Authorization": f"Bearer {valid_token}"}
        for i in range(5):
            resp = await client.get("/api/v1/narrative", headers=headers)
            assert resp.status_code == 200, f"Request {i + 1} failed unexpectedly"

        resp = await client.get("/api/v1/narrative", headers=headers)
        assert resp.status_code == 429


# ── Test: Error response shape ──────────────────────────────


class TestRateLimitErrorShape:
    async def test_429_matches_error_response_schema(self, client: AsyncClient) -> None:
        for _ in range(100):
            await client.get("/health")

        resp = await client.get("/health")
        assert resp.status_code == 429
        assert resp.headers["content-type"] == "application/json"
        body = resp.json()
        assert "detail" in body
        assert body["detail"] == "Rate limit exceeded. Try again later."


# ── Test: Redis fallback ────────────────────────────────────


class TestRedisFallback:
    def test_app_starts_with_redis_unavailable(self, caplog: pytest.LogCaptureFixture) -> None:
        with patch("app.limiter.redis_lib.from_url") as mock_redis:
            mock_redis.return_value.ping.side_effect = ConnectionError("Connection refused")
            with caplog.at_level(logging.WARNING, logger="app.limiter"):
                from app.limiter import _build_limiter

                lim = _build_limiter()
            assert lim is not None
            assert "Redis unavailable" in caplog.text

    async def test_health_returns_200_after_redis_failure(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200


# ── Test: Limit reset after window ─────────────────────────


class TestLimitReset:
    async def test_limit_resets_after_window(self, client: AsyncClient) -> None:
        for _ in range(100):
            await client.get("/health")

        resp = await client.get("/health")
        assert resp.status_code == 429

        # Reset the storage to simulate time window expiry
        fresh = MemoryStorage()
        limiter._storage = fresh
        limiter._limiter.storage = fresh

        resp = await client.get("/health")
        assert resp.status_code == 200
