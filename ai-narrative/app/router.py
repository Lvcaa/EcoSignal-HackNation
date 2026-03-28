"""EcoSignal AI Narrative — HTTP router."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import get_llm_client
from app.schemas import NarrativeRequest, NarrativeResponse
from app.service import generate_narrative

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/generate", response_model=NarrativeResponse)
async def post_generate(request: NarrativeRequest) -> NarrativeResponse:
    """Generate a personalised climate narrative for the user."""
    client = get_llm_client()
    result = await generate_narrative(request, client)
    logger.info(
        "Narrative generated for user %s at %s (fallback=%s)",
        result.user_id,
        result.generated_at,
        result.is_fallback,
    )
    return result
