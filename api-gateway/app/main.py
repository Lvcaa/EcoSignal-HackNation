from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.limiter import limiter
from app.router import (
    actions_router,
    auth_router,
    community_router,
    env_router,
    footprint_router,
    narrative_router,
    profile_router,
)

settings = get_settings()

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EcoSignal API Gateway",
    version="1.0.0",
    description=(
        "Public API for EcoSignal — connects Italian citizens' daily habits "
        "to real local environmental data, generating personalized climate "
        "narratives and actionable CO₂-reduction suggestions."
    ),
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(profile_router, prefix=API_PREFIX)
app.include_router(footprint_router, prefix=API_PREFIX)
app.include_router(env_router, prefix=API_PREFIX)
app.include_router(narrative_router, prefix=API_PREFIX)
app.include_router(actions_router, prefix=API_PREFIX)
app.include_router(community_router, prefix=API_PREFIX)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    _unused = (request, exc)
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    _ = request
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _ = request
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
