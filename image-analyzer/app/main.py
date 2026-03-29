"""EcoSignal Image Analyzer Service — FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.climatiq import ClimatiqClient
from app.config import get_settings
from app.router import router
from app.schemas import ErrorResponse

settings = get_settings()

logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Store Climatiq client in app.state for use at request time."""
    client = ClimatiqClient(api_key=settings.climatiq_api_key)
    app.state.climatiq = client
    if client.enabled:
        logging.getLogger(__name__).info("Climatiq client initialized (API key set)")
    else:
        logging.getLogger(__name__).info("Climatiq client disabled (no API key), using fallback factors")
    yield


app = FastAPI(
    title="EcoSignal Image Analyzer Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error").model_dump(),
    )
