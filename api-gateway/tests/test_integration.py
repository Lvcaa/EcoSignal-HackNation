from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import timedelta
from typing import Any

import httpx
import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt
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


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Override conftest client — raise_app_exceptions=False for proper HTTP error testing."""
    app.dependency_overrides[get_settings] = _test_settings
    transport = ASGITransport(app=app, raise_app_exceptions=False)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/profile"),
    ("POST", "/api/v1/footprint/calculate"),
    ("GET", "/api/v1/footprint/history"),
    ("GET", "/api/v1/env/air-quality"),
    ("GET", "/api/v1/env/climate-context"),
    ("GET", "/api/v1/narrative"),
    ("GET", "/api/v1/actions"),
    ("GET", "/api/v1/community/stats"),
]


@pytest.fixture(autouse=True)
def _reset_limiter() -> None:
    """Reset limiter to fresh in-memory storage before each test."""
    fresh = MemoryStorage()
    limiter._storage = fresh
    limiter._limiter.storage = fresh


@pytest.fixture
def valid_token() -> str:
    return create_access_token({"sub": TEST_USER_ID})


def _make_downstream_token_response() -> dict[str, Any]:
    token = create_access_token({"sub": TEST_USER_ID})
    return {
        "user_id": TEST_USER_ID,
        "access_token": token,
        "refresh_token": "refresh-placeholder",
        "token_type": "bearer",
        "expires_in": 3600,
    }


# ── Auth flow (happy path) ───────────────────────────────────


class TestAuthFlowHappyPath:
    async def test_register_returns_201_with_token(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_make_downstream_token_response())
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_returns_200_with_token(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_make_downstream_token_response())
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "securepass1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body

    async def test_refresh_returns_200_with_new_token(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_make_downstream_token_response())
        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "old-refresh-token"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body

    async def test_register_token_contains_correct_sub(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(json=_make_downstream_token_response())
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "new2@example.com", "password": "securepass1"},
        )
        body = resp.json()
        settings = get_settings()
        decoded = jwt.decode(
            body["access_token"],
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        assert decoded["sub"] == TEST_USER_ID


# ── 401 edge cases (unauthenticated) ─────────────────────────


class TestProtectedEndpoints401:
    @pytest.mark.parametrize("method,path", PROTECTED_ENDPOINTS)
    @pytest.mark.parametrize(
        "auth_mode",
        ["missing", "expired", "wrong_secret", "wrong_format"],
    )
    async def test_returns_401_for_bad_auth(
        self,
        client: AsyncClient,
        method: str,
        path: str,
        auth_mode: str,
    ) -> None:
        headers: dict[str, str] = {}
        if auth_mode == "expired":
            token = create_access_token(
                {"sub": TEST_USER_ID}, expires_delta=timedelta(seconds=-1)
            )
            headers["Authorization"] = f"Bearer {token}"
        elif auth_mode == "wrong_secret":
            token = jwt.encode(
                {"sub": TEST_USER_ID, "exp": 9999999999, "iat": 1000000000},
                "wrong-secret",
                algorithm="HS256",
            )
            headers["Authorization"] = f"Bearer {token}"
        elif auth_mode == "wrong_format":
            headers["Authorization"] = "Token some-token-value"
        # "missing" → no Authorization header at all

        resp = await client.request(method, path, headers=headers)
        assert resp.status_code == 401


# ── 401 / error edge cases (downstream failure) ──────────────


class TestDownstreamFailures:
    async def test_downstream_401_forwarded_not_500(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_response(
            json={"detail": "Invalid credentials"},
            status_code=401,
        )
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "wrongpass1"},
        )
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Invalid credentials"

    async def test_downstream_unreachable_returns_error(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        httpx_mock.add_exception(httpx.ConnectError("Connection refused"))
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com", "password": "securepass1"},
        )
        # _proxy does not catch ConnectError → generic_exception_handler → 500
        assert resp.status_code == 500


# ── 422 edge cases (validation) ──────────────────────────────


class TestValidation422:
    async def test_register_missing_fields_returns_422(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post("/api/v1/auth/register", json={})
        assert resp.status_code == 422

    async def test_register_invalid_email_returns_422(
        self, client: AsyncClient
    ) -> None:
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "securepass1"},
        )
        assert resp.status_code == 422

    async def test_login_empty_password_returns_422(
        self, client: AsyncClient
    ) -> None:
        # LoginRequest.password is a required field — omitting it triggers 422
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@example.com"},
        )
        assert resp.status_code == 422


# ── Rate limit integration (full stack) ──────────────────────


class TestRateLimitIntegration:
    async def test_register_11th_returns_429(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        for _ in range(10):
            httpx_mock.add_response(json=_make_downstream_token_response())
        body = {"email": "rl@example.com", "password": "securepass1"}
        for i in range(10):
            resp = await client.post("/api/v1/auth/register", json=body)
            assert resp.status_code == 201, f"Request {i + 1} failed"
        resp = await client.post("/api/v1/auth/register", json=body)
        assert resp.status_code == 429

    async def test_login_21st_returns_429(
        self, client: AsyncClient, httpx_mock: Any
    ) -> None:
        for _ in range(20):
            httpx_mock.add_response(json=_make_downstream_token_response())
        body = {"email": "rl@example.com", "password": "securepass1"}
        for i in range(20):
            resp = await client.post("/api/v1/auth/login", json=body)
            assert resp.status_code == 200, f"Request {i + 1} failed"
        resp = await client.post("/api/v1/auth/login", json=body)
        assert resp.status_code == 429

    async def test_narrative_6th_returns_429(
        self, client: AsyncClient, httpx_mock: Any, valid_token: str
    ) -> None:
        for _ in range(5):
            httpx_mock.add_response(json={"headline": "test narrative"})
        headers = {"Authorization": f"Bearer {valid_token}"}
        for i in range(5):
            resp = await client.get("/api/v1/narrative", headers=headers)
            assert resp.status_code == 200, f"Request {i + 1} failed"
        resp = await client.get("/api/v1/narrative", headers=headers)
        assert resp.status_code == 429


# ── /health sanity ───────────────────────────────────────────


class TestHealthSanity:
    async def test_health_no_auth_returns_200(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.status_code == 200

    async def test_health_response_body(self, client: AsyncClient) -> None:
        resp = await client.get("/health")
        assert resp.json() == {"status": "ok", "version": "1.0.0"}
