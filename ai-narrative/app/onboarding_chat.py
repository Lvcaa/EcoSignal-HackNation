"""EcoSignal AI Narrative — conversational onboarding via Regolo AI.

Guides the user through onboarding questions in a natural Italian conversation,
extracting structured profile data from their responses.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import REGOLO_MODEL

logger = logging.getLogger(__name__)

# Regex to find a JSON object in the LLM response even with surrounding text
_JSON_RE = re.compile(r"\{[\s\S]*\}", re.DOTALL)

ONBOARDING_SYSTEM_PROMPT = """\
Sei Green Buddy, un assistente amichevole che aiuta gli utenti a configurare il loro profilo ambientale attraverso una conversazione naturale in italiano.

Il tuo obiettivo è raccogliere queste informazioni in modo conversazionale e naturale:

1. **address** — L'indirizzo completo dove vivono (via, numero, città). Da questo puoi estrarre anche il **zip_code** (CAP, 5 cifre) se lo forniscono o lo conosci per la zona. Se non riesci a ricavare il CAP dall'indirizzo, chiedilo esplicitamente.
2. **zip_code** — CAP (codice di avviamento postale italiano, 5 cifre). Estrailo dall'indirizzo se possibile.
3. **transport_mode** — Come si spostano principalmente: "car", "transit", "bike", "walk", "mixed"
4. **commute_days_per_week** — Quanti giorni a settimana si spostano per lavoro/studio (0-7)
5. **diet_type** — Tipo di dieta: "meat_daily", "meat_weekly", "vegetarian", "vegan"
6. **home_type** — Tipo di abitazione: "apartment", "house"
7. **home_size_sqm** — Dimensione dell'abitazione in metri quadri (10-300)
8. **has_pets** — Se hanno animali domestici (true/false)
9. **pet_type** — Se sì, tipo: "dog", "cat", "small_animal" (null se no)
10. **pet_count** — Numero di animali (0 se no)

Regole:
- Parla SEMPRE in italiano, con tono caldo e amichevole
- Fai UNA o DUE domande alla volta, mai di più
- Sii naturale: non sembrare un questionario, ma un amico curioso
- Quando l'utente risponde, conferma brevemente e passa alla domanda successiva
- Se una risposta è ambigua, chiedi gentilmente di chiarire
- Non essere troppo lungo — risposte brevi e amichevoli
- Inizia presentandoti brevemente e chiedendo dove vivono (indirizzo)

Rispondi SEMPRE con un JSON valido con questa struttura:
{
  "message": "<il tuo messaggio all'utente>",
  "extracted_data": {
    // solo i campi che sei riuscito a estrarre dalle risposte finora
    // usa null per i campi non ancora raccolti
  },
  "complete": false  // true solo quando HAI TUTTI i dati necessari
}

Quando complete è true, il messaggio finale deve essere un breve riepilogo entusiasta di quello che hai scoperto.
Non aggiungere mai markdown, solo JSON puro.
"""


def _parse_llm_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from the LLM response, tolerating extra text."""
    # Strip markdown code fences
    clean = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass
    # Try to find a JSON object anywhere in the text
    match = _JSON_RE.search(clean)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    # Last resort: treat entire text as the message
    logger.warning("Could not parse JSON from LLM response: %s", text[:200])
    return {"message": text.strip(), "extracted_data": {}, "complete": False}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call_chat_llm(
    messages: list[dict[str, str]],
    client: OpenAI,
) -> dict[str, Any]:
    """Call Regolo AI with the full conversation history."""
    response = client.chat.completions.create(
        model=REGOLO_MODEL,
        max_tokens=800,
        timeout=30,
        messages=messages,
    )
    text: str = response.choices[0].message.content or ""
    return _parse_llm_json(text)


def _rebuild_for_llm(
    conversation: list[dict[str, str]],
    extracted_data: dict[str, Any],
) -> list[dict[str, str]]:
    """Rebuild conversation so assistant messages are valid JSON for the LLM.

    The frontend stores assistant content as plain text (the message field only).
    The LLM expects its own responses to be JSON. We wrap them back.
    """
    rebuilt: list[dict[str, str]] = []
    for msg in conversation:
        if msg["role"] == "assistant":
            # Wrap plain-text assistant message back into the JSON format the LLM expects
            wrapped = json.dumps(
                {"message": msg["content"], "extracted_data": extracted_data, "complete": False},
                ensure_ascii=False,
            )
            rebuilt.append({"role": "assistant", "content": wrapped})
        else:
            rebuilt.append(msg)
    return rebuilt


async def chat_onboarding(
    conversation: list[dict[str, str]],
    extracted_data: dict[str, Any],
    client: OpenAI,
) -> dict[str, Any]:
    """Process a conversational onboarding turn.

    Args:
        conversation: List of {"role": "user"/"assistant", "content": "..."} messages.
                      The last message should be from the user (or empty for the first turn).
        extracted_data: Accumulated extracted data from previous turns.
        client: Regolo AI OpenAI-compatible client.

    Returns:
        {"message": str, "extracted_data": dict, "complete": bool}
    """
    llm_messages = [{"role": "system", "content": ONBOARDING_SYSTEM_PROMPT}]

    if not conversation:
        # First turn: AI introduces itself
        llm_messages.append(
            {"role": "user", "content": "[L'utente ha appena aperto la chat. Presentati e fai la prima domanda.]"}
        )
    else:
        llm_messages.extend(_rebuild_for_llm(conversation, extracted_data))

    try:
        result = await asyncio.to_thread(_call_chat_llm, llm_messages, client)
        # Merge newly extracted data with accumulated data
        new_data = {**extracted_data}
        for k, v in result.get("extracted_data", {}).items():
            if v is not None:
                new_data[k] = v
        return {
            "message": result.get("message", ""),
            "extracted_data": new_data,
            "complete": result.get("complete", False),
        }
    except Exception:
        logger.warning("Chat onboarding LLM call failed", exc_info=True)
        return {
            "message": "Scusa, ho avuto un piccolo problema. Puoi ripetere?",
            "extracted_data": extracted_data,
            "complete": False,
        }
