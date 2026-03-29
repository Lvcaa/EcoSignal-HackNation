"""EcoSignal Image Analyzer — API router."""
from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas import ImageAnalysisRequest, ImageAnalysisResponse
from app.service import analyze_image

router = APIRouter()


@router.post("/api/v1/analyze", response_model=ImageAnalysisResponse)
async def post_analyze(body: ImageAnalysisRequest, request: Request) -> ImageAnalysisResponse:
    settings = get_settings()
    climatiq = getattr(request.app.state, "climatiq", None)
    return await analyze_image(body, settings, climatiq=climatiq)
