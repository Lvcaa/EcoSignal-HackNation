from __future__ import annotations

from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from jose import jwt

from app.auth import create_access_token, hash_password, verify_password
from app.config import get_settings

TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"


# ── create_access_token ───────────────────────────────────


class TestCreateAccessToken:
    def test_returns_nonempty_string(self) -> None:
        token = create_access_token({"sub": TEST_USER_ID})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_payload_contains_correct_claims(self) -> None:
        token = create_access_token({"sub": TEST_USER_ID})
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["sub"] == TEST_USER_ID
        assert "exp" in payload
        assert "iat" in payload

    def test_custom_expires_delta(self) -> None:
        delta = timedelta(minutes=5)
        token = create_access_token({"sub": TEST_USER_ID}, expires_delta=delta)
        settings = get_settings()
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        assert payload["exp"] - payload["iat"] == 5 * 60


# ── verify_token (via TestClient) ─────────────────────────


class TestVerifyToken:
    @pytest.fixture
    def valid_token(self) -> str:
        return create_access_token({"sub": TEST_USER_ID})

    @patch("app.router._proxy", new_callable=AsyncMock, return_value={"ok": True})
    async def test_valid_token_returns_payload(
        self,
        mock_proxy: AsyncMock,
        client,  # type: ignore[no-untyped-def]
        valid_token: str,
    ) -> None:
        response = await client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {valid_token}"},
        )
        assert response.status_code == 200

    async def test_expired_token_returns_401(self, client) -> None:  # type: ignore[no-untyped-def]
        token = create_access_token(
            {"sub": TEST_USER_ID},
            expires_delta=timedelta(seconds=-1),
        )
        response = await client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"

    async def test_tampered_token_returns_401(self, client) -> None:  # type: ignore[no-untyped-def]
        token = jwt.encode(
            {"sub": TEST_USER_ID, "exp": 9999999999, "iat": 1000000000},
            "wrong-secret",
            algorithm="HS256",
        )
        response = await client.get(
            "/api/v1/profile",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401

    async def test_missing_auth_header_returns_401(self, client) -> None:  # type: ignore[no-untyped-def]
        response = await client.get("/api/v1/profile")
        assert response.status_code == 401

    async def test_malformed_bearer_returns_401(self, client) -> None:  # type: ignore[no-untyped-def]
        response = await client.get(
            "/api/v1/profile",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        assert response.status_code == 401


# ── Password hashing ─────────────────────────────────────


class TestPasswordHashing:
    def test_hash_differs_from_plain(self) -> None:
        plain = "my-secure-password"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_verify_correct_password(self) -> None:
        plain = "my-secure-password"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self) -> None:
        hashed = hash_password("correct-password")
        assert verify_password("wrong-password", hashed) is False

    def test_two_hashes_differ_salt(self) -> None:
        plain = "same-password"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
