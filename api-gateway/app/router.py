from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.auth import verify_token
from app.config import Settings, get_settings
from app.limiter import limiter
from app.schemas import ErrorResponse, LoginRequest, RegisterRequest, TokenPayload


async def _proxy(
    method: str,
    url: str,
    json: Any | None = None,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.request(method, url, json=json, params=params, headers=headers)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Downstream error"))
    return response.json()


def _auth_headers(request: Request) -> dict[str, str]:
    """Extract Authorization header from incoming request for forwarding."""
    auth = request.headers.get("authorization")
    return {"Authorization": auth} if auth else {}


# ── Auth Router ────────────────────────────────────────────

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post(
    "/register",
    status_code=201,
    responses={400: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
@limiter.limit("10/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.user_profile_service_url}/api/v1/auth/register",
        json=body.model_dump(),
    )


@auth_router.post(
    "/login",
    responses={401: {"model": ErrorResponse}},
)
@limiter.limit("20/minute")
async def login(
    request: Request,
    body: LoginRequest,
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.user_profile_service_url}/api/v1/auth/login",
        json=body.model_dump(),
    )


@auth_router.post(
    "/refresh",
    responses={401: {"model": ErrorResponse}},
)
async def refresh(
    body: dict[str, str],
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.user_profile_service_url}/api/v1/auth/refresh",
        json=body,
    )


# ── Profile Router ─────────────────────────────────────────

profile_router = APIRouter(prefix="/profile", tags=["profile"])


@profile_router.post(
    "/onboarding",
    status_code=201,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def submit_onboarding(
    request: Request,
    body: dict[str, Any],
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.user_profile_service_url}/api/v1/onboarding",
        json={**body, "user_id": token.sub},
        headers=_auth_headers(request),
    )


@profile_router.get(
    "",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def get_profile(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.user_profile_service_url}/api/v1/profile",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@profile_router.patch(
    "",
    responses={400: {"model": ErrorResponse}, 401: {"model": ErrorResponse}},
)
async def update_profile(
    request: Request,
    body: dict[str, Any],
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "PATCH",
        f"{settings.user_profile_service_url}/api/v1/profile",
        json={**body, "user_id": token.sub},
        headers=_auth_headers(request),
    )


# ── Footprint Router ──────────────────────────────────────

footprint_router = APIRouter(prefix="/footprint", tags=["footprint"])


@footprint_router.post(
    "/calculate",
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def calculate_footprint(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    # Fetch user profile to get all fields needed for footprint calculation
    profile = await _proxy(
        "GET",
        f"{settings.user_profile_service_url}/api/v1/profile",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )
    return await _proxy(
        "POST",
        f"{settings.footprint_service_url}/api/v1/footprint/calculate",
        json={
            "user_id": token.sub,
            "transport_mode": profile.get("transport_mode"),
            "diet_type": profile.get("diet_type"),
            "home_type": profile.get("home_type"),
            "home_size_sqm": profile.get("home_size_sqm"),
            "commute_days_per_week": profile.get("commute_days_per_week", 5),
            "pet_type": profile.get("pet_type"),
            "pet_count": profile.get("pet_count", 0),
        },
        headers=_auth_headers(request),
    )


@footprint_router.get(
    "/history",
    responses={401: {"model": ErrorResponse}},
)
async def get_footprint_history(
    request: Request,
    weeks: int = Query(default=8, ge=1, le=8),
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.footprint_service_url}/api/v1/footprint/history",
        params={"user_id": token.sub, "weeks": weeks},
        headers=_auth_headers(request),
    )


# ── Env Router ─────────────────────────────────────────────

env_router = APIRouter(prefix="/env", tags=["env"])


@env_router.get(
    "/air-quality",
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_air_quality(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.env_data_service_url}/api/v1/env/air-quality",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@env_router.get(
    "/climate-context",
    responses={401: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_climate_context(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.env_data_service_url}/api/v1/env/climate-context",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


# ── Narrative Router ───────────────────────────────────────

narrative_router = APIRouter(prefix="/narrative", tags=["narrative"])


@narrative_router.get(
    "",
    responses={
        401: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
@limiter.limit("5/minute")
async def get_narrative(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.ai_narrative_service_url}/api/v1/narrative",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


# ── Actions Router ─────────────────────────────────────────

actions_router = APIRouter(prefix="/actions", tags=["actions"])


@actions_router.get(
    "",
    responses={401: {"model": ErrorResponse}},
)
async def get_actions(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.post(
    "/{action_id}/complete",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def complete_action(
    request: Request,
    action_id: str,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.actions_service_url}/api/v1/actions/{action_id}/complete",
        json={"user_id": token.sub},
        headers=_auth_headers(request),
    )


# ── Community Router ───────────────────────────────────────

community_router = APIRouter(prefix="/community", tags=["community"])


@community_router.get(
    "/stats",
    responses={401: {"model": ErrorResponse}},
)
async def get_community_stats(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.community_service_url}/api/v1/community/stats",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@community_router.post(
    "/challenge/join",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def join_challenge(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.community_service_url}/api/v1/community/challenge/join",
        json={"user_id": token.sub},
        headers=_auth_headers(request),
    )


# Fix: @limiter.limit wrappers have __globals__ from slowapi, not this module.
# With `from __future__ import annotations`, string annotations can't resolve
# types like RegisterRequest in slowapi's namespace. Inject them explicitly.
_module_types = {k: v for k, v in globals().items() if not k.startswith("_")}
for _fn in (register, login, get_narrative):
    _fn.__globals__.update(_module_types)
