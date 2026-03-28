"""EcoSignal AI Narrative — core business logic.

Zero imports from fastapi. LLM client is always injected.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import REGOLO_MODEL
from app.prompt import SYSTEM_PROMPT, build_user_message
from app.schemas import NarrativeRequest, NarrativeResponse

logger = logging.getLogger(__name__)


def _build_fallback(user_id: object) -> NarrativeResponse:
    """Return a static fallback narrative for the given user."""
    return NarrativeResponse(
        user_id=user_id,  # type: ignore[arg-type]
        headline="Ogni piccolo gesto conta per il nostro pianeta.",
        body=(
            "Le tue scelte quotidiane hanno un impatto reale sull'ambiente "
            "che ti circonda. Continuare a monitorare le proprie abitudini "
            "è già un primo passo importante."
        ),
        local_context=(
            "I dati ambientali locali sono temporaneamente non disponibili."
        ),
        source_note="EcoSignal · Dati aggiornati periodicamente",
        generated_at=datetime.now(timezone.utc),
        is_fallback=True,
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_llm(
    system: str,
    user_msg: str,
    client: OpenAI,
) -> dict[str, str]:
    """Call Regolo AI (OpenAI-compatible) synchronously with retry."""
    response = client.chat.completions.create(
        model=REGOLO_MODEL,
        max_tokens=1000,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_msg},
        ],
    )
    text: str = response.choices[0].message.content or ""
    clean = text.strip().removeprefix("```json").removesuffix("```").strip()
    return json.loads(clean)  # type: ignore[no-any-return]


async def generate_narrative(
    request: NarrativeRequest,
    client: OpenAI,
) -> NarrativeResponse:
    """Generate an LLM-powered narrative, with fallback on any error."""
    user_msg = build_user_message(request)

    try:
        raw = await asyncio.to_thread(
            _call_llm, SYSTEM_PROMPT, user_msg, client
        )

        headline = raw.get("headline", "")
        if len(headline) > 120:
            raw["headline"] = headline[:117] + "..."

        parsed = NarrativeResponse(
            user_id=request.user_id,
            generated_at=datetime.now(timezone.utc),
            is_fallback=False,
            **raw,
        )

        return parsed

    except Exception:
        logger.warning(
            "Narrative generation failed for user %s, returning fallback",
            request.user_id,
            exc_info=True,
        )
        return _build_fallback(request.user_id)
