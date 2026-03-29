"""Pure business logic — no FastAPI, no direct DB calls."""

from __future__ import annotations

from uuid import UUID

from app.auth import create_access_token, hash_password, verify_password
from app.exceptions import InvalidCredentialsError
from app.repository import UserRepository
from app.schemas import (
    ProfileUpdateRequest,
    TokenPayload,
    TokenResponse,
    UserProfileResponse,
)


async def register_user(
    repo: UserRepository,
    email: str,
    display_name: str,
    password: str,
) -> TokenResponse:
    hashed = hash_password(password)
    user = await repo.create_user(email, display_name, hashed)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


async def login_user(
    repo: UserRepository,
    email: str,
    password: str,
) -> TokenResponse:
    user = await repo.get_by_email(email)
    if user is None:
        raise InvalidCredentialsError
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


async def refresh_token(
    repo: UserRepository,
    token_payload: TokenPayload,
) -> TokenResponse:
    user = await repo.get_by_id(UUID(token_payload.sub))
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(access_token=token)


async def impersonate_user(
    repo: UserRepository,
    user_id: UUID,
) -> TokenResponse:
    """Issue a token for any user by ID (demo/pitch only)."""
    user = await repo.get_by_id(user_id)
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        display_name=user.display_name,
    )


async def get_profile(
    repo: UserRepository,
    user_id: UUID,
) -> UserProfileResponse:
    user = await repo.get_by_id(user_id)
    return UserProfileResponse.model_validate(user, from_attributes=True)


async def update_profile(
    repo: UserRepository,
    user_id: UUID,
    update_data: ProfileUpdateRequest,
) -> UserProfileResponse:
    fields = update_data.model_dump(exclude_none=True)
    user = await repo.update_profile(user_id, **fields)
    return UserProfileResponse.model_validate(user, from_attributes=True)
