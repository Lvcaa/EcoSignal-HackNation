"""HTTP layer tests for app.router."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import mock_llm_response, valid_request


@pytest.mark.asyncio
async def test_post_generate_success(async_client: AsyncClient) -> None:
    """POST /generate with valid body returns 200 + NarrativeResponse."""
    client = mock_llm_response()
    with patch("app.router.get_llm_client", return_value=client):
        resp = await async_client.post(
            "/generate", json=valid_request().model_dump(mode="json")
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_fallback"] is False
    assert "headline" in data
    assert "body" in data
    assert "local_context" in data
    assert "source_note" in data
    assert "generated_at" in data


@pytest.mark.asyncio
async def test_post_generate_fallback_on_failure(
    async_client: AsyncClient,
) -> None:
    """LLM failure still returns 200 with is_fallback=True."""
    client = MagicMock()
    client.chat.completions.create.side_effect = Exception("boom")
    with patch("app.router.get_llm_client", return_value=client):
        resp = await async_client.post(
            "/generate", json=valid_request().model_dump(mode="json")
        )
    assert resp.status_code == 200
    assert resp.json()["is_fallback"] is True


@pytest.mark.asyncio
async def test_post_generate_missing_user_id(
    async_client: AsyncClient,
) -> None:
    """Missing user_id returns 422."""
    payload = valid_request().model_dump(mode="json")
    del payload["user_id"]
    resp = await async_client.post("/generate", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_generate_invalid_uuid(
    async_client: AsyncClient,
) -> None:
    """Invalid UUID format returns 422."""
    payload = valid_request().model_dump(mode="json")
    payload["user_id"] = "not-a-uuid"
    resp = await async_client.post("/generate", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health(async_client: AsyncClient) -> None:
    """GET /health returns status ok."""
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}
