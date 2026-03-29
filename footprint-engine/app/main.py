"""FastAPI application for EcoSignal Footprint Engine."""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.climatiq import ClimatiqClient
from app.config import get_settings
from app.factors import load_factors
from app.schemas import FootprintRequest, FootprintResult
from app.service import calculate_footprint

settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load Climatiq factors on startup."""
    client = ClimatiqClient(api_key=settings.climatiq_api_key)
    await load_factors(client)
    yield


app = FastAPI(title="EcoSignal Footprint Engine", lifespan=lifespan)

router = APIRouter(prefix="/api/v1/footprint")


@router.post("/calculate", response_model=FootprintResult)
def post_calculate(body: FootprintRequest) -> FootprintResult:
    try:
        return calculate_footprint(body)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


app.include_router(router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def generic_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
