from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import Settings, get_settings
from app.main import app


def get_test_settings() -> Settings:
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
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_settings] = get_test_settings
    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def mock_downstream(httpx_mock: Any) -> Any:
    """Fixture that provides httpx_mock for mocking downstream service calls."""
    return httpx_mock
