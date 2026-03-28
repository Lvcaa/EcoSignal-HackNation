"""Test fixtures for actions-engine."""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.catalogue import load_catalogue
from app.models import Base
from app.repository import ActionRepository
from app.router import _get_session

ROME_TZ = ZoneInfo("Europe/Rome")

engine = create_async_engine("sqlite+aiosqlite://", echo=False)
test_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db() -> AsyncGenerator[None, None]:
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session


@pytest.fixture
def action_repository(async_session: AsyncSession) -> ActionRepository:
    return ActionRepository(async_session)


@pytest.fixture
def valid_user_id() -> uuid.UUID:
    return uuid.UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture(autouse=True)
def _load_catalogue() -> None:
    """Load the real catalogue.json for all tests."""
    load_catalogue("catalogue.json")


@pytest.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient wired to the FastAPI app with test DB session."""
    from app.main import app

    async def override_session() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    app.dependency_overrides[_get_session] = override_session

    transport = ASGITransport(app=app)  # type: ignore[arg-type]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def seed_completion(
    repo: ActionRepository,
    user_id: uuid.UUID,
    action_id: str,
    target_date: date,
) -> None:
    """Helper: insert a completion record for a specific date."""
    dt = datetime(
        target_date.year, target_date.month, target_date.day, 12, 0, 0, tzinfo=ROME_TZ
    )
    await repo.complete_action(user_id, action_id, dt)
    await repo.session.commit()
