"""EcoSignal Image Analyzer — core analysis logic using Claude Vision API."""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings
from app.prompts import CLOTHING_PROMPT, GROCERY_PROMPT, MEAL_PROMPT
from app.schemas import (
    AnalysisType,
    ClothingAnalysisResult,
    Confidence,
    GroceryAnalysisResult,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    MealAnalysisResult,
)

logger = logging.getLogger(__name__)

PROMPT_MAP = {
    AnalysisType.meal: MEAL_PROMPT,
    AnalysisType.grocery: GROCERY_PROMPT,
    AnalysisType.clothing: CLOTHING_PROMPT,
}

RESULT_MAP = {
    AnalysisType.meal: MealAnalysisResult,
    AnalysisType.grocery: GroceryAnalysisResult,
    AnalysisType.clothing: ClothingAnalysisResult,
}


def _build_fallback(analysis_type: AnalysisType) -> ImageAnalysisResponse:
    result_cls = RESULT_MAP[analysis_type]
    return ImageAnalysisResponse(
        analysis_type=analysis_type,
        result=result_cls(items=[], total_co2_kg=0.0, confidence=Confidence.low),
        analyzed_at=datetime.now(timezone.utc),
        is_fallback=True,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_claude(
    prompt: str,
    content_blocks: list,
    client: Anthropic,
    model: str,
) -> dict:
    response = client.messages.create(
        model=model,
        max_tokens=1500,
        system=prompt,
        messages=[{"role": "user", "content": content_blocks}],
    )
    text = response.content[0].text
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(clean)


async def analyze_image(
    request: ImageAnalysisRequest,
    settings: Settings,
) -> ImageAnalysisResponse:
    prompt = PROMPT_MAP[request.analysis_type]

    # Build content blocks
    content_blocks: list = []
    if request.image_base64:
        content_blocks.append(
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": request.image_base64,
                },
            }
        )
    if request.user_description:
        content_blocks.append({"type": "text", "text": request.user_description})
    elif not request.image_base64:
        return _build_fallback(request.analysis_type)

    client = Anthropic(api_key=settings.anthropic_api_key)

    try:
        raw = await asyncio.to_thread(
            _call_claude, prompt, content_blocks, client, settings.model_name
        )
        result_cls = RESULT_MAP[request.analysis_type]
        result = result_cls(**raw)
        return ImageAnalysisResponse(
            analysis_type=request.analysis_type,
            result=result,
            analyzed_at=datetime.now(timezone.utc),
            is_fallback=False,
        )
    except Exception:
        logger.warning("Image analysis failed, returning fallback", exc_info=True)
        return _build_fallback(request.analysis_type)
