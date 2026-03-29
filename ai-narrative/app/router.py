"""EcoSignal AI Narrative — HTTP router."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.config import get_llm_client
from app.onboarding_chat import chat_onboarding
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


# ── Conversational Onboarding ────────────────────────────────


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatOnboardingRequest(BaseModel):
    messages: list[ChatMessage] = Field(default_factory=list)
    extracted_data: dict[str, Any] = Field(default_factory=dict)


class ChatOnboardingResponse(BaseModel):
    message: str
    extracted_data: dict[str, Any]
    complete: bool


@router.post("/chat/onboarding", response_model=ChatOnboardingResponse)
async def post_chat_onboarding(body: ChatOnboardingRequest) -> ChatOnboardingResponse:
    """Process one turn of the conversational onboarding chat."""
    client = get_llm_client()
    conversation = [{"role": m.role, "content": m.content} for m in body.messages]
    result = await chat_onboarding(conversation, body.extracted_data, client)
    return ChatOnboardingResponse(**result)
