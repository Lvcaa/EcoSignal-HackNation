from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
