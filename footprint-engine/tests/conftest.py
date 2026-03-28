"""Shared fixtures for footprint-engine tests."""

from collections.abc import AsyncGenerator
from datetime import date, timedelta
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.enums import DietType, HomeType, TransportMode
from app.main import app
from app.schemas import FootprintRequest

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _next_monday() -> date:
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        return today
    return today + timedelta(days=days_ahead)


def _test_settings() -> Settings:
    return Settings(log_level="DEBUG")


app.dependency_overrides[get_settings] = _test_settings


@pytest.fixture
def valid_request() -> FootprintRequest:
    return FootprintRequest(
        user_id=TEST_USER_ID,
        transport_mode=TransportMode.car,
        diet_type=DietType.meat_weekly,
        home_type=HomeType.apartment,
        home_size_sqm=70,
        week_start=_next_monday(),
    )


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
