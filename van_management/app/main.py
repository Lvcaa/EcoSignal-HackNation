from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.signals import router as signals_router
from app.api.v1.trucks import router as trucks_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.schemas.common import ApiResponse

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# TODO: restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trucks_router)
app.include_router(signals_router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Safety net: if all retries in the service layer are exhausted, return 409
    instead of letting an unhandled IntegrityError become a 500."""
    return JSONResponse(
        status_code=409,
        content={
            "success": False,
            "message": "Version conflict: concurrent write detected, please retry",
            "data": None,
        },
    )


@app.get("/health", tags=["meta"], response_model=ApiResponse)
def health() -> ApiResponse:
    return ApiResponse(success=True, message="OK")


@app.get("/version", tags=["meta"], response_model=ApiResponse)
def version() -> ApiResponse:
    return ApiResponse(
        success=True,
        message="Service info",
        data={"name": settings.APP_NAME, "version": settings.APP_VERSION},
    )


# --- Future TODOs ---
# TODO: Add authentication / API key middleware
# TODO: Add WebSocket endpoint for live truck position streaming
# TODO: Add Kafka / event-streaming ingestion
# TODO: Add route entities and route-optimization endpoints
# TODO: Add map-tile integration helpers
