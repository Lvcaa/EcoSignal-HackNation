"""HTTP-layer integration tests for footprint-engine."""

from datetime import date, timedelta

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USER_ID


def _next_monday() -> date:
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        return today
    return today + timedelta(days=days_ahead)


MONDAY = _next_monday()
TUESDAY = MONDAY + timedelta(days=1)

VALID_BODY = {
    "user_id": str(TEST_USER_ID),
    "transport_mode": "car",
    "diet_type": "meat_weekly",
    "home_type": "apartment",
    "home_size_sqm": 70,
    "week_start": MONDAY.isoformat(),
}


# ── POST /api/v1/footprint/calculate ──────────────────────────


@pytest.mark.anyio
async def test_calculate_valid(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/footprint/calculate", json=VALID_BODY)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_kg_co2" in data
    assert "breakdown" in data
    assert "label" in data


@pytest.mark.anyio
async def test_calculate_tuesday_422(client: AsyncClient) -> None:
    body = {**VALID_BODY, "week_start": TUESDAY.isoformat()}
    resp = await client.post("/api/v1/footprint/calculate", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_calculate_missing_user_id(client: AsyncClient) -> None:
    body = {k: v for k, v in VALID_BODY.items() if k != "user_id"}
    resp = await client.post("/api/v1/footprint/calculate", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_calculate_invalid_transport_mode(client: AsyncClient) -> None:
    body = {**VALID_BODY, "transport_mode": "helicopter"}
    resp = await client.post("/api/v1/footprint/calculate", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_calculate_home_size_zero(client: AsyncClient) -> None:
    body = {**VALID_BODY, "home_size_sqm": 0}
    resp = await client.post("/api/v1/footprint/calculate", json=body)
    assert resp.status_code == 422


@pytest.mark.anyio
async def test_expected_total_76_6(client: AsyncClient) -> None:
    """Manually computed: car 150*0.170=25.5, meat_weekly=24.5, apt 70*0.38=26.6 → 76.6."""
    resp = await client.post("/api/v1/footprint/calculate", json=VALID_BODY)
    assert resp.status_code == 200
    assert resp.json()["total_kg_co2"] == 76.6


# ── GET /health ────────────────────────────────────────────────


@pytest.mark.anyio
async def test_health(client: AsyncClient) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "version": "1.0.0"}
