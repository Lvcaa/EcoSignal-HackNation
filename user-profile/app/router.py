from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import service
from app.auth import verify_token
from app.config import async_session_maker
from app.exceptions import EmailAlreadyExistsError, InvalidCredentialsError, UserNotFoundError
from app.models import User
from app.repository import UserRepository
from app.schemas import (
    ErrorResponse,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    TokenPayload,
    TokenResponse,
    UserProfileResponse,
)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    async with async_session_maker() as session:
        yield session  # type: ignore[misc]


async def get_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


async def get_current_user(
    token: TokenPayload = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
) -> User:
    repo = UserRepository(session)
    try:
        return await repo.get_by_id(UUID(token.sub))
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


# ── Auth Router ───────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/register", status_code=201, response_model=TokenResponse)
async def register(
    body: RegisterRequest,
    repo: UserRepository = Depends(get_repository),
) -> TokenResponse:
    try:
        return await service.register_user(
            repo, body.email, body.display_name, body.password
        )
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )


@auth_router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    repo: UserRepository = Depends(get_repository),
) -> TokenResponse:
    try:
        return await service.login_user(repo, body.email, body.password)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh(
    token_payload: TokenPayload = Depends(verify_token),
    repo: UserRepository = Depends(get_repository),
) -> TokenResponse:
    return await service.refresh_token(repo, token_payload)


@auth_router.get("/users")
async def list_users(
    _token: TokenPayload = Depends(verify_token),
    limit: int = Query(default=50, ge=1, le=200),
    repo: UserRepository = Depends(get_repository),
) -> list[dict]:
    """List all users (demo/pitch only)."""
    users = await repo.list_users(limit)
    return [
        {"user_id": str(u.id), "display_name": u.display_name, "email": u.email, "zip_code": u.zip_code}
        for u in users
    ]


@auth_router.post("/impersonate/{user_id}", response_model=TokenResponse)
async def impersonate(
    user_id: UUID,
    _token: TokenPayload = Depends(verify_token),
    repo: UserRepository = Depends(get_repository),
) -> TokenResponse:
    """Issue a token for any user by ID (demo/pitch only)."""
    try:
        return await service.impersonate_user(repo, user_id)
    except UserNotFoundError:
        raise HTTPException(status_code=404, detail="User not found")


# ── Profile Router ────────────────────────────────────────────

profile_router = APIRouter(tags=["profile"])


@profile_router.post(
    "/onboarding",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def submit_onboarding(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    repo: UserRepository = Depends(get_repository),
) -> UserProfileResponse:
    if user.onboarding_complete:
        return UserProfileResponse.model_validate(user, from_attributes=True)
    return await service.update_profile(repo, user.id, body)


@profile_router.get(
    "/profile",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_profile(
    user: User = Depends(get_current_user),
) -> UserProfileResponse:
    return UserProfileResponse.model_validate(user, from_attributes=True)


@profile_router.patch(
    "/profile",
    response_model=UserProfileResponse,
    responses={404: {"model": ErrorResponse}},
)
async def patch_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    repo: UserRepository = Depends(get_repository),
) -> UserProfileResponse:
    fields = body.model_dump(exclude_none=True)
    return await service.update_profile(
        repo, user.id, ProfileUpdateRequest(**fields)
    )
