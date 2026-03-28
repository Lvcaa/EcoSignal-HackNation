from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings, get_settings
from app.models import Base
from app.repository import UserRepository

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


def _test_settings() -> Settings:
    return Settings(
        database_url=TEST_DATABASE_URL,
        secret_key="test-secret-key",
        algorithm="HS256",
        access_token_expire_minutes=60,
        log_level="DEBUG",
    )


@pytest.fixture(autouse=True)
async def _setup_db() -> AsyncIterator[None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_session() -> AsyncIterator[AsyncSession]:
    async with test_session_maker() as session:
        yield session


@pytest.fixture
async def user_repository(async_session: AsyncSession) -> UserRepository:
    return UserRepository(async_session)


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app
    from app.router import get_session

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with test_session_maker() as session:
            yield session

    app.dependency_overrides[get_settings] = _test_settings
    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
