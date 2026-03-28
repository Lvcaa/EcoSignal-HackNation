"""EcoSignal Image Analyzer — API router."""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings
from app.schemas import ImageAnalysisRequest, ImageAnalysisResponse
from app.service import analyze_image

router = APIRouter()


@router.post("/api/v1/analyze", response_model=ImageAnalysisResponse)
async def post_analyze(request: ImageAnalysisRequest) -> ImageAnalysisResponse:
    settings = get_settings()
    return await analyze_image(request, settings)
