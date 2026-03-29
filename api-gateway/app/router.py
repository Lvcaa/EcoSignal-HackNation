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
    timeout: float = 10.0,
) -> Any:
    async with httpx.AsyncClient(timeout=timeout) as client:
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


@auth_router.get(
    "/users",
    responses={401: {"model": ErrorResponse}},
)
async def list_users(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    """List all users (demo/pitch only)."""
    return await _proxy(
        "GET",
        f"{settings.user_profile_service_url}/api/v1/auth/users",
        params={"limit": limit},
        headers=_auth_headers(request),
    )


@auth_router.post(
    "/impersonate/{user_id}",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
async def impersonate(
    request: Request,
    user_id: str,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    """Issue a token for any user by ID (demo/pitch only)."""
    return await _proxy(
        "POST",
        f"{settings.user_profile_service_url}/api/v1/auth/impersonate/{user_id}",
        headers=_auth_headers(request),
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
        timeout=60.0,  # LLM narrative generation needs more time
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


@actions_router.get(
    "/streak",
    responses={401: {"model": ErrorResponse}},
)
async def get_streak(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/streak",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.post(
    "/log",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def log_action(
    request: Request,
    body: dict[str, Any],
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.actions_service_url}/api/v1/actions/log",
        json={**body, "user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.get(
    "/daily",
    responses={401: {"model": ErrorResponse}},
)
async def get_daily_actions(
    request: Request,
    date: str = Query(...),
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/daily",
        params={"user_id": token.sub, "date": date},
        headers=_auth_headers(request),
    )


@actions_router.get(
    "/monthly",
    responses={401: {"model": ErrorResponse}},
)
async def get_monthly_summary(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/monthly",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.get(
    "/weekly",
    responses={401: {"model": ErrorResponse}},
)
async def get_weekly_summary(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/weekly",
        params={"user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.post(
    "/weekly-survey",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def submit_weekly_survey(
    request: Request,
    body: dict[str, Any],
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.actions_service_url}/api/v1/actions/weekly-survey",
        json={**body, "user_id": token.sub},
        headers=_auth_headers(request),
    )


@actions_router.get(
    "/weekly-survey/latest",
    responses={401: {"model": ErrorResponse}},
)
async def get_latest_survey(
    request: Request,
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/weekly-survey/latest",
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


# ── Chat Onboarding Router (no auth — pre-registration) ───

chat_router = APIRouter(prefix="/chat", tags=["chat"])


@chat_router.post(
    "/onboarding",
    responses={422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
@limiter.limit("30/minute")
async def chat_onboarding(
    request: Request,
    body: dict[str, Any],
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.ai_narrative_service_url}/chat/onboarding",
        json=body,
        timeout=60.0,
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


@community_router.get(
    "/leaderboard",
    responses={401: {"model": ErrorResponse}},
)
async def get_leaderboard(
    request: Request,
    zip_code: str | None = Query(None),
    limit: int = Query(default=50, ge=1, le=100),
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    params: dict[str, Any] = {"limit": limit}
    if zip_code:
        params["zip_code"] = zip_code
    return await _proxy(
        "GET",
        f"{settings.community_service_url}/api/v1/community/leaderboard",
        params=params,
        headers=_auth_headers(request),
    )


@community_router.get(
    "/user/{target_user_id}/actions",
    responses={401: {"model": ErrorResponse}},
)
async def get_user_actions(
    request: Request,
    target_user_id: str,
    date: str = Query(None),
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    """Get a user's daily actions (public community view)."""
    params: dict[str, Any] = {"user_id": target_user_id}
    if date:
        params["date"] = date
    return await _proxy(
        "GET",
        f"{settings.actions_service_url}/api/v1/actions/daily",
        params=params,
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


# ── Image Router ──────────────────────────────────────────

image_router = APIRouter(prefix="/image", tags=["image"])


@image_router.post(
    "/analyze",
    responses={401: {"model": ErrorResponse}, 422: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
@limiter.limit("20/minute")
async def analyze_image(
    request: Request,
    body: dict[str, Any],
    token: TokenPayload = Depends(verify_token),
    settings: Settings = Depends(get_settings),
) -> Any:
    return await _proxy(
        "POST",
        f"{settings.image_analyzer_service_url}/api/v1/analyze",
        json={**body, "user_id": token.sub},
        headers=_auth_headers(request),
        timeout=60.0,  # Claude Vision needs more time for image analysis
    )


# Fix: @limiter.limit wrappers have __globals__ from slowapi, not this module.
# With `from __future__ import annotations`, string annotations can't resolve
# types like RegisterRequest in slowapi's namespace. Inject them explicitly.
_module_types = {k: v for k, v in globals().items() if not k.startswith("_")}
for _fn in (register, login, get_narrative, analyze_image, chat_onboarding):
    _fn.__globals__.update(_module_types)
