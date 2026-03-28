"""Unit tests for service.py — pure logic, no HTTP."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.config import get_settings
from app.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
)
from app.repository import UserRepository
from app.schemas import ProfileUpdateRequest, TokenPayload
from app.service import (
    get_profile,
    login_user,
    refresh_token,
    register_user,
    update_profile,
)

pytestmark = pytest.mark.asyncio


# ── register_user ─────────────────────────────────────────────


async def test_register_user_happy_path(user_repository: UserRepository) -> None:
    result = await register_user(
        user_repository, "alice@example.com", "Alice", "securepass123"
    )
    assert result.token_type == "bearer"
    assert result.access_token


async def test_register_user_duplicate_email(
    user_repository: UserRepository,
) -> None:
    await register_user(
        user_repository, "bob@example.com", "Bob", "securepass123"
    )
    with pytest.raises(EmailAlreadyExistsError):
        await register_user(
            user_repository, "bob@example.com", "Bob2", "securepass456"
        )


async def test_register_user_token_contains_user_id(
    user_repository: UserRepository,
) -> None:
    from jose import jwt

    result = await register_user(
        user_repository, "carol@example.com", "Carol", "securepass123"
    )
    settings = get_settings()
    payload = jwt.decode(
        result.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    sub = payload["sub"]
    # Verify it's a valid UUID
    UUID(sub)


# ── login_user ────────────────────────────────────────────────


async def test_login_user_happy_path(user_repository: UserRepository) -> None:
    await register_user(
        user_repository, "dave@example.com", "Dave", "securepass123"
    )
    result = await login_user(user_repository, "dave@example.com", "securepass123")
    assert result.token_type == "bearer"
    assert result.access_token


async def test_login_user_wrong_email(user_repository: UserRepository) -> None:
    with pytest.raises(InvalidCredentialsError):
        await login_user(user_repository, "nobody@example.com", "securepass123")


async def test_login_user_wrong_password(user_repository: UserRepository) -> None:
    await register_user(
        user_repository, "eve@example.com", "Eve", "securepass123"
    )
    with pytest.raises(InvalidCredentialsError):
        await login_user(user_repository, "eve@example.com", "wrongpassword")


# ── refresh_token ─────────────────────────────────────────────


async def test_refresh_token_happy_path(user_repository: UserRepository) -> None:
    from datetime import datetime, timezone

    reg = await register_user(
        user_repository, "frank@example.com", "Frank", "securepass123"
    )
    from jose import jwt

    settings = get_settings()
    payload = jwt.decode(
        reg.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    token_payload = TokenPayload(
        sub=payload["sub"],
        exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
    )
    result = await refresh_token(user_repository, token_payload)
    assert result.access_token
    assert result.token_type == "bearer"
    # Verify the refreshed token contains the same user
    new_payload = jwt.decode(
        result.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    assert new_payload["sub"] == payload["sub"]


async def test_refresh_token_deleted_user(user_repository: UserRepository) -> None:
    from datetime import datetime, timezone

    token_payload = TokenPayload(
        sub="00000000-0000-0000-0000-000000000000",
        exp=datetime.now(timezone.utc),
        iat=datetime.now(timezone.utc),
    )
    with pytest.raises(UserNotFoundError):
        await refresh_token(user_repository, token_payload)


# ── get_profile ───────────────────────────────────────────────


async def test_get_profile_before_onboarding(
    user_repository: UserRepository,
) -> None:
    from jose import jwt

    reg = await register_user(
        user_repository, "grace@example.com", "Grace", "securepass123"
    )
    settings = get_settings()
    payload = jwt.decode(
        reg.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    profile = await get_profile(user_repository, UUID(payload["sub"]))
    assert profile.onboarding_complete is False


async def test_get_profile_after_onboarding(
    user_repository: UserRepository,
) -> None:
    from jose import jwt

    reg = await register_user(
        user_repository, "heidi@example.com", "Heidi", "securepass123"
    )
    settings = get_settings()
    payload = jwt.decode(
        reg.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    user_id = UUID(payload["sub"])
    await update_profile(
        user_repository,
        user_id,
        ProfileUpdateRequest(
            zip_code="00100",
            transport_mode="bike",
            diet_type="vegan",
            home_type="apartment",
            home_size_sqm=60,
        ),
    )
    profile = await get_profile(user_repository, user_id)
    assert profile.onboarding_complete is True


# ── update_profile ────────────────────────────────────────────


async def test_update_profile_partial(user_repository: UserRepository) -> None:
    from jose import jwt

    reg = await register_user(
        user_repository, "ivan@example.com", "Ivan", "securepass123"
    )
    settings = get_settings()
    payload = jwt.decode(
        reg.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    user_id = UUID(payload["sub"])
    # Set zip_code first
    await update_profile(
        user_repository,
        user_id,
        ProfileUpdateRequest(zip_code="20100"),
    )
    # Set transport_mode — zip_code should remain
    profile = await update_profile(
        user_repository,
        user_id,
        ProfileUpdateRequest(transport_mode="car"),
    )
    assert profile.zip_code == "20100"
    assert profile.transport_mode == "car"


async def test_update_profile_full_onboarding(
    user_repository: UserRepository,
) -> None:
    from jose import jwt

    reg = await register_user(
        user_repository, "judy@example.com", "Judy", "securepass123"
    )
    settings = get_settings()
    payload = jwt.decode(
        reg.access_token, settings.secret_key, algorithms=[settings.algorithm]
    )
    user_id = UUID(payload["sub"])
    profile = await update_profile(
        user_repository,
        user_id,
        ProfileUpdateRequest(
            zip_code="00100",
            transport_mode="transit",
            diet_type="vegetarian",
            home_type="house",
            home_size_sqm=120,
        ),
    )
    assert profile.onboarding_complete is True
    assert profile.zip_code == "00100"
    assert profile.home_size_sqm == 120
