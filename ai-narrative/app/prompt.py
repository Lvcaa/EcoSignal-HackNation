"""EcoSignal AI Narrative — prompt templates for Claude.

No imports from fastapi or anthropic allowed in this file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas import NarrativeRequest

SYSTEM_PROMPT: str = """\
You are Green Buddy's climate narrative engine. Your job is to write a \
short, warm, non-alarmist message in Italian that connects a user's \
weekly habits and daily actions to real local environmental data.

Rules:
- Always write in Italian
- Be human, specific, and end with one encouraging sentence
- Never use technical jargon
- Never blame or shame the user
- Always ground the narrative in the actual numbers provided
- If baseline and current week CO2 are provided, compare them: \
"Questa settimana il tuo impatto è X% [inferiore/superiore] rispetto alla tua baseline"
- If daily actions are provided, give specific feedback on the most \
impactful ones, e.g. "Il pasto di oggi ha aggiunto 2.3 kg CO₂ — un po' sopra la media"
- Keep the tone warm and encouraging, like a supportive friend
- If air or climate data is marked as fallback, do not mention \
specific air quality or temperature numbers — speak in general terms
- Respond ONLY with a valid JSON object. No markdown, no preamble.

JSON schema to follow exactly:
{
  "headline": "<1 sentence, max 120 chars, warm and specific>",
  "body": "<2-3 sentences connecting habits, daily actions, and baseline comparison to local data>",
  "local_context": "<1 sentence about today's local conditions>",
  "source_note": "<attribution, e.g. Basato su dati ISPRA 2024 · OpenAQ oggi>"
}
"""

ITALIAN_TRANSPORT_LABELS: dict[str, str] = {
    "car": "auto",
    "transit": "mezzi pubblici",
    "bike": "bicicletta",
    "walk": "a piedi",
    "mixed": "auto e mezzi pubblici",
}

ITALIAN_DIET_LABELS: dict[str, str] = {
    "meat_daily": "con carne ogni giorno",
    "meat_weekly": "con carne qualche volta a settimana",
    "vegetarian": "vegetariana",
    "vegan": "vegana",
}


def build_user_message(request: NarrativeRequest) -> str:
    """Build the user message string from a NarrativeRequest.

    Includes all numeric context and flags fallback data clearly.
    """
    transport_label = ITALIAN_TRANSPORT_LABELS.get(
        request.transport_mode.value, request.transport_mode.value
    )
    diet_label = ITALIAN_DIET_LABELS.get(
        request.diet_type.value, request.diet_type.value
    )

    city_display = request.city or "N/D"
    avg_pct = request.vs_national_avg_pct * 100

    if request.air_is_fallback:
        air_section = "Qualità dell'aria: dati non disponibili (fallback)"
    else:
        air_section = (
            f"Qualità dell'aria oggi: PM2.5 {request.pm25} µg/m³ "
            f"({request.aqi_label})"
        )

    if request.climate_is_fallback:
        climate_section = "Contesto climatico: dati non disponibili (fallback)"
    else:
        climate_section = (
            f"Temperatura attuale: {request.current_temp_c}°C, "
            f"anomalia: {request.anomaly_label}"
        )

    transport_kg = request.breakdown.get("transport_kg", 0.0)
    food_kg = request.breakdown.get("food_kg", 0.0)
    home_kg = request.breakdown.get("home_kg", 0.0)

    # Baseline comparison section
    baseline_section = ""
    if request.baseline_co2_kg is not None and request.current_week_co2_kg is not None:
        if request.baseline_co2_kg > 0:
            delta_pct = (
                (request.current_week_co2_kg - request.baseline_co2_kg)
                / request.baseline_co2_kg
            ) * 100
            direction = "inferiore" if delta_pct < 0 else "superiore"
            baseline_section = (
                f"\nBaseline settimanale: {request.baseline_co2_kg:.1f} kg CO₂\n"
                f"CO₂ questa settimana: {request.current_week_co2_kg:.1f} kg CO₂\n"
                f"Variazione: {abs(delta_pct):.1f}% {direction} rispetto alla baseline\n"
            )

    # Daily actions section
    actions_section = ""
    if request.daily_actions:
        actions_lines = ["Azioni di oggi:"]
        for action in request.daily_actions:
            actions_lines.append(
                f"  - {action.type}: {action.description} ({action.co2_kg:.1f} kg CO₂)"
            )
        actions_section = "\n" + "\n".join(actions_lines) + "\n"

    return (
        f"Città: {city_display}, CAP: {request.zip_code}\n"
        f"Trasporto: {transport_label}\n"
        f"Dieta: {diet_label}\n"
        f"Abitazione: {request.home_type.value}, {request.home_size_sqm} m²\n"
        f"\n"
        f"Impronta settimanale: {request.total_kg_co2} kg CO₂\n"
        f"  - Trasporto: {transport_kg} kg\n"
        f"  - Alimentazione: {food_kg} kg\n"
        f"  - Casa: {home_kg} kg\n"
        f"Confronto media nazionale: {avg_pct:+.1f}%\n"
        f"Livello: {request.label}\n"
        f"{baseline_section}"
        f"{actions_section}"
        f"\n"
        f"{air_section}\n"
        f"{climate_section}"
    )
