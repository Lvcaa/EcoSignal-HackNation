"""EcoSignal Image Analyzer — two-step analysis:
1. Regolo AI (Mistral Vision) identifies items (name, portion, category)
2. Climatiq API estimates CO2 for each identified item
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.climatiq import ClimatiqClient
from app.config import REGOLO_MODEL, Settings, get_vision_client
from app.factors import estimate_clothing_co2, estimate_grocery_co2, estimate_meal_co2
from app.prompts import CLOTHING_PROMPT, GROCERY_PROMPT, MEAL_PROMPT
from app.schemas import (
    AnalysisType,
    ClothingAnalysisResult,
    ClothingItem,
    Confidence,
    GroceryAnalysisResult,
    GroceryItem,
    ImageAnalysisRequest,
    ImageAnalysisResponse,
    MealAnalysisResult,
    MealItem,
)

logger = logging.getLogger(__name__)

PROMPT_MAP = {
    AnalysisType.meal: MEAL_PROMPT,
    AnalysisType.grocery: GROCERY_PROMPT,
    AnalysisType.clothing: CLOTHING_PROMPT,
}


def _build_fallback(analysis_type: AnalysisType) -> ImageAnalysisResponse:
    result_map = {
        AnalysisType.meal: MealAnalysisResult,
        AnalysisType.grocery: GroceryAnalysisResult,
        AnalysisType.clothing: ClothingAnalysisResult,
    }
    result_cls = result_map[analysis_type]
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
def _call_regolo(
    system_prompt: str,
    user_content: list,
    client: OpenAI,
) -> dict:
    """Call Regolo AI (Mistral Vision) via OpenAI-compatible API."""
    response = client.chat.completions.create(
        model=REGOLO_MODEL,
        max_tokens=1500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    text = response.choices[0].message.content
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(clean)


async def analyze_image(
    request: ImageAnalysisRequest,
    settings: Settings,
    climatiq: ClimatiqClient | None = None,
) -> ImageAnalysisResponse:
    """Analyze image: Regolo AI identifies items, Climatiq estimates CO2."""
    prompt = PROMPT_MAP[request.analysis_type]

    # Build content blocks (OpenAI vision format)
    user_content: list = []
    if request.image_base64:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{request.image_base64}",
                },
            }
        )
    if request.user_description:
        user_content.append({"type": "text", "text": request.user_description})
    elif not request.image_base64:
        return _build_fallback(request.analysis_type)

    vision_client = get_vision_client()

    try:
        # Step 1: Regolo AI identifies items
        raw = await asyncio.to_thread(
            _call_regolo, prompt, user_content, vision_client
        )
        logger.info("Regolo identified items: %s", raw)

        identified_items = raw.get("items", [])
        confidence = raw.get("confidence", "medium")

        # Step 2: Climatiq estimates CO2 for each item
        if request.analysis_type == AnalysisType.meal:
            enriched = await estimate_meal_co2(identified_items, climatiq)
            total_co2 = round(sum(i["estimated_co2_kg"] for i in enriched), 4)
            result = MealAnalysisResult(
                items=[MealItem(
                    name=i["name"],
                    portion_g=i.get("portion_g", 0.0),
                    estimated_co2_kg=i["estimated_co2_kg"],
                ) for i in enriched],
                total_co2_kg=total_co2,
                confidence=Confidence(confidence),
            )

        elif request.analysis_type == AnalysisType.grocery:
            enriched = await estimate_grocery_co2(identified_items, climatiq)
            total_co2 = round(sum(i["estimated_co2_kg"] for i in enriched), 4)
            result = GroceryAnalysisResult(
                items=[GroceryItem(
                    name=i["name"],
                    quantity=i.get("quantity", 1),
                    category=i.get("category", "altro"),
                    estimated_co2_kg=i["estimated_co2_kg"],
                ) for i in enriched],
                total_co2_kg=total_co2,
                confidence=Confidence(confidence),
            )

        elif request.analysis_type == AnalysisType.clothing:
            enriched = await estimate_clothing_co2(identified_items, climatiq)
            total_co2 = round(sum(i["estimated_co2_kg"] for i in enriched), 4)
            result = ClothingAnalysisResult(
                items=[ClothingItem(
                    type=i.get("type", ""),
                    material=i.get("material", "misti"),
                    brand_guess=i.get("brand_guess"),
                    estimated_co2_kg=i["estimated_co2_kg"],
                ) for i in enriched],
                total_co2_kg=total_co2,
                confidence=Confidence(confidence),
            )
        else:
            return _build_fallback(request.analysis_type)

        return ImageAnalysisResponse(
            analysis_type=request.analysis_type,
            result=result,
            analyzed_at=datetime.now(timezone.utc),
            is_fallback=False,
        )

    except Exception:
        logger.warning("Image analysis failed, returning fallback", exc_info=True)
        return _build_fallback(request.analysis_type)
