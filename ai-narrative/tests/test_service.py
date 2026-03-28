"""Unit tests for app.service — mock OpenAI-compatible (Regolo) SDK."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

from openai import APIConnectionError
import pytest

from app.service import generate_narrative
from tests.conftest import (
    MOCK_VALID_RESPONSE_JSON,
    mock_llm_response,
    valid_request,
)


@pytest.mark.asyncio
async def test_happy_path(mock_client: MagicMock) -> None:
    """Valid LLM response produces is_fallback=False."""
    req = valid_request()
    result = await generate_narrative(req, mock_client)

    assert result.is_fallback is False
    assert result.user_id == req.user_id
    assert len(result.headline) <= 120
    assert (datetime.now(timezone.utc) - result.generated_at).seconds < 5


@pytest.mark.asyncio
async def test_headline_truncation() -> None:
    """Headlines longer than 120 chars get truncated with '...'."""
    long_headline = "A" * 150
    payload = json.loads(MOCK_VALID_RESPONSE_JSON)
    payload["headline"] = long_headline
    client = mock_llm_response(json.dumps(payload))

    result = await generate_narrative(valid_request(), client)

    assert result.is_fallback is False
    assert len(result.headline) == 120
    assert result.headline.endswith("...")


@pytest.mark.asyncio
async def test_json_fence_stripping() -> None:
    """LLM response wrapped in ```json fences is parsed correctly."""
    fenced = f"```json\n{MOCK_VALID_RESPONSE_JSON}\n```"
    client = mock_llm_response(fenced)

    result = await generate_narrative(valid_request(), client)

    assert result.is_fallback is False


@pytest.mark.asyncio
async def test_retry_succeeds_on_third_attempt() -> None:
    """LLM fails twice then succeeds — no fallback."""
    client = MagicMock()
    message = MagicMock()
    message.content = MOCK_VALID_RESPONSE_JSON
    choice = MagicMock()
    choice.message = message
    success_response = MagicMock()
    success_response.choices = [choice]

    client.chat.completions.create.side_effect = [
        APIConnectionError(request=MagicMock()),
        APIConnectionError(request=MagicMock()),
        success_response,
    ]

    result = await generate_narrative(valid_request(), client)

    assert result.is_fallback is False
    assert client.chat.completions.create.call_count == 3


@pytest.mark.asyncio
async def test_all_retries_exhausted() -> None:
    """All 3 attempts fail — returns fallback."""
    client = MagicMock()
    client.chat.completions.create.side_effect = APIConnectionError(
        request=MagicMock()
    )

    req = valid_request()
    result = await generate_narrative(req, client)

    assert result.is_fallback is True
    assert result.user_id == req.user_id
    assert (datetime.now(timezone.utc) - result.generated_at).seconds < 5


@pytest.mark.asyncio
async def test_invalid_json_returns_fallback() -> None:
    """Non-JSON LLM output triggers fallback."""
    client = mock_llm_response("This is not JSON at all")

    result = await generate_narrative(valid_request(), client)

    assert result.is_fallback is True


@pytest.mark.asyncio
async def test_pydantic_validation_failure_returns_fallback() -> None:
    """Valid JSON but missing required field triggers fallback."""
    incomplete = json.dumps(
        {
            "body": "some body",
            "local_context": "some context",
            "source_note": "some note",
        }
    )
    client = mock_llm_response(incomplete)

    result = await generate_narrative(valid_request(), client)

    assert result.is_fallback is True
