"""Shared fixtures for ai-narrative tests."""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.schemas import NarrativeRequest

TEST_USER_ID = UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")

MOCK_VALID_RESPONSE_JSON = json.dumps(
    {
        "headline": "Questa settimana hai prodotto 76.6 kg di CO₂ a Roma.",
        "body": (
            "I tuoi spostamenti in auto rappresentano la parte principale "
            "della tua impronta. Oggi la qualità dell'aria a Roma è nella "
            "norma, con PM2.5 a 18.5 µg/m³."
        ),
        "local_context": (
            "La temperatura attuale è di 22.3°C, circa 2.1°C "
            "sopra la media storica per questo periodo."
        ),
        "source_note": "Basato su dati ISPRA 2024 · OpenAQ oggi",
    }
)


def valid_request(**overrides: object) -> NarrativeRequest:
    """Build a realistic NarrativeRequest for testing."""
    defaults: dict[str, object] = {
        "user_id": TEST_USER_ID,
        "transport_mode": "car",
        "diet_type": "meat_weekly",
        "home_type": "apartment",
        "home_size_sqm": 70,
        "total_kg_co2": 76.6,
        "vs_national_avg_pct": 0.08,
        "breakdown": {
            "transport_kg": 34.2,
            "food_kg": 22.1,
            "home_kg": 20.3,
        },
        "label": "average",
        "zip_code": "00100",
        "city": "Roma",
        "pm25": 18.5,
        "aqi_label": "moderate",
        "current_temp_c": 22.3,
        "anomaly_c": 2.1,
        "anomaly_label": "+2.1°C above historical average",
        "air_is_fallback": False,
        "climate_is_fallback": False,
    }
    defaults.update(overrides)
    return NarrativeRequest(**defaults)  # type: ignore[arg-type]


def mock_llm_response(text: str = MOCK_VALID_RESPONSE_JSON) -> MagicMock:
    """Create a mock OpenAI-compatible client that returns the given text."""
    client = MagicMock()
    message = MagicMock()
    message.content = text
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    client.chat.completions.create.return_value = response
    return client


@pytest.fixture
def mock_client() -> MagicMock:
    """Default mock LLM client returning valid JSON."""
    return mock_llm_response()


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
