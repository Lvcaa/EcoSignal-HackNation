"""EcoSignal AI Narrative Service — FastAPI application entry point."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.router import router
from app.schemas import ErrorResponse

settings = get_settings()
logging.basicConfig(level=settings.log_level)

app = FastAPI(title="EcoSignal AI Narrative Service", version="1.0.0")
app.include_router(router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Catch-all — should never fire since service.py handles everything."""
    logging.getLogger(__name__).error("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(detail="Internal server error").model_dump(),
    )
