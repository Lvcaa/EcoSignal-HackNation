"""EcoSignal Image Analyzer — core analysis logic (placeholder)."""
from __future__ import annotations

from app.config import Settings
from app.schemas import ImageAnalysisRequest, ImageAnalysisResponse


async def analyze_image(request: ImageAnalysisRequest, settings: Settings) -> ImageAnalysisResponse:
    raise NotImplementedError("analyze_image not yet implemented")
