"""HTTP layer tests for router.py."""

from __future__ import annotations

from typing import Any

import pytest
from httpx import AsyncClient

from app.auth import create_access_token

pytestmark = pytest.mark.asyncio

REGISTER_URL = "/api/v1/auth/register"
LOGIN_URL = "/api/v1/auth/login"
REFRESH_URL = "/api/v1/auth/refresh"
ONBOARDING_URL = "/api/v1/onboarding"
PROFILE_URL = "/api/v1/profile"
HEALTH_URL = "/health"

VALID_USER: dict[str, str] = {
    "email": "test@example.com",
    "display_name": "Test User",
    "password": "securepass123",
}

FULL_ONBOARDING: dict[str, Any] = {
    "zip_code": "00100",
    "transport_mode": "bike",
    "diet_type": "vegan",
    "home_type": "apartment",
    "home_size_sqm": 60,
}

FAKE_USER_ID = "00000000-0000-0000-0000-000000000000"


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _fake_token() -> str:
    result: str = create_access_token({"sub": FAKE_USER_ID})  # type: ignore[no-any-return]
    return result


async def _register(client: AsyncClient) -> str:
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    token: str = resp.json()["access_token"]
    return token


# ── POST /auth/register ──────────────────────────────────────


async def test_register_success(client: AsyncClient) -> None:
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 201
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(REGISTER_URL, json=VALID_USER)
    assert resp.status_code == 409


# ── POST /auth/login ─────────────────────────────────────────


async def test_login_valid(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(
        LOGIN_URL,
        json={"email": "test@example.com", "password": "securepass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient) -> None:
    await client.post(REGISTER_URL, json=VALID_USER)
    resp = await client.post(
        LOGIN_URL,
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


# ── POST /auth/refresh ───────────────────────────────────────


async def test_refresh_valid_token(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.post(REFRESH_URL, headers=_auth_header(token))
    assert resp.status_code == 200
    assert "access_token" in resp.json()


# ── POST /onboarding ─────────────────────────────────────────


async def test_onboarding_valid(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.post(
        ONBOARDING_URL, json=FULL_ONBOARDING, headers=_auth_header(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarding_complete"] is True


async def test_onboarding_invalid_zip(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.post(
        ONBOARDING_URL,
        json={"zip_code": "123456"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


# ── GET /profile ──────────────────────────────────────────────


async def test_get_profile_with_token(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.get(PROFILE_URL, headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


async def test_get_profile_no_token(client: AsyncClient) -> None:
    resp = await client.get(PROFILE_URL)
    assert resp.status_code == 401


# ── PATCH /profile ────────────────────────────────────────────


async def test_patch_profile_empty_body(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.patch(
        PROFILE_URL, json={}, headers=_auth_header(token)
    )
    assert resp.status_code == 422


# ── GET /health ───────────────────────────────────────────────


async def test_health(client: AsyncClient) -> None:
    resp = await client.get(HEALTH_URL)
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}


# ── GET /profile (extended) ─────────────────────────────────


async def test_get_profile_no_onboarding(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.get(PROFILE_URL, headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["onboarding_complete"] is False


async def test_get_profile_full_onboarding(client: AsyncClient) -> None:
    token = await _register(client)
    await client.post(ONBOARDING_URL, json=FULL_ONBOARDING, headers=_auth_header(token))
    resp = await client.get(PROFILE_URL, headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["onboarding_complete"] is True


async def test_get_profile_deleted_user(client: AsyncClient) -> None:
    token = _fake_token()
    resp = await client.get(PROFILE_URL, headers=_auth_header(token))
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


# ── PATCH /profile (extended) ────────────────────────────────


async def test_patch_profile_partial_zip_only(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.patch(
        PROFILE_URL, json={"zip_code": "20100"}, headers=_auth_header(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["zip_code"] == "20100"
    assert body["transport_mode"] is None


async def test_patch_profile_full_update(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.patch(
        PROFILE_URL, json=FULL_ONBOARDING, headers=_auth_header(token)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarding_complete"] is True
    assert body["zip_code"] == "00100"
    assert body["home_size_sqm"] == 60


async def test_patch_profile_invalid_zip_letters(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.patch(
        PROFILE_URL, json={"zip_code": "abcde"}, headers=_auth_header(token)
    )
    assert resp.status_code == 422


async def test_patch_profile_invalid_transport_mode(client: AsyncClient) -> None:
    token = await _register(client)
    resp = await client.patch(
        PROFILE_URL, json={"transport_mode": "helicopter"}, headers=_auth_header(token)
    )
    assert resp.status_code == 422


async def test_patch_profile_deleted_user(client: AsyncClient) -> None:
    token = _fake_token()
    resp = await client.patch(
        PROFILE_URL, json={"zip_code": "00100"}, headers=_auth_header(token)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"


# ── POST /onboarding (extended) ──────────────────────────────


async def test_onboarding_idempotent(client: AsyncClient) -> None:
    token = await _register(client)
    resp1 = await client.post(
        ONBOARDING_URL, json=FULL_ONBOARDING, headers=_auth_header(token)
    )
    assert resp1.status_code == 200
    assert resp1.json()["onboarding_complete"] is True
    resp2 = await client.post(
        ONBOARDING_URL, json=FULL_ONBOARDING, headers=_auth_header(token)
    )
    assert resp2.status_code == 200
    assert resp2.json()["onboarding_complete"] is True


async def test_onboarding_invalid_home_size_zero(client: AsyncClient) -> None:
    token = await _register(client)
    body = {**FULL_ONBOARDING, "home_size_sqm": 0}
    resp = await client.post(
        ONBOARDING_URL, json=body, headers=_auth_header(token)
    )
    assert resp.status_code == 422


async def test_onboarding_deleted_user(client: AsyncClient) -> None:
    token = _fake_token()
    resp = await client.post(
        ONBOARDING_URL, json=FULL_ONBOARDING, headers=_auth_header(token)
    )
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found"
