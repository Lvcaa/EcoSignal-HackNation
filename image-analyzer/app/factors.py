"""CO2 estimation for identified items via Climatiq API with fallbacks.

Step 1: Claude Vision identifies items (name, portion, category)
Step 2: This module estimates CO2 for each item using Climatiq or fallbacks

Climatiq activity IDs use weight-based factors from CONCITO/Agribalyse datasets.
Region "FR" is used as CONCITO has the most complete food lifecycle data.
"""

from __future__ import annotations

import logging
from typing import Any

from app.climatiq import ClimatiqClient

logger = logging.getLogger(__name__)

# ── Fallback CO2 factors (ISPRA 2023 / Poore & Nemecek 2018) ───

# Per kg of food product (kg CO2e / kg food)
FOOD_CO2_PER_KG: dict[str, float] = {
    "carne_rossa": 27.0,
    "pollo": 6.9,
    "pesce": 6.0,
    "latticini": 3.3,
    "verdure": 2.0,
    "verdure_fresche": 2.0,
    "frutta": 1.0,
    "frutta_fresca": 1.0,
    "cereali_pasta": 1.4,
    "cereali_pasta_riso": 1.4,
    "bevande": 1.5,
    "surgelati": 3.5,
    "snack_dolci": 2.5,
    "altro": 2.0,
}

# Per kg of textile material (kg CO2e / kg textile)
CLOTHING_CO2_PER_KG: dict[str, float] = {
    "cotone": 16.0,
    "poliestere": 24.0,
    "lana": 20.0,
    "lino": 10.0,
    "nylon": 22.0,
    "seta": 18.0,
    "misti": 18.0,
    "pelle": 34.0,
}

# ── Climatiq weight-based activity IDs ──────────────────────────
# Source: CONCITO (food-type_*) — weight-based, unit=kg/kg
# Source: Bafa/CAEP (textiles-type_*) — weight-based, unit=kg/kg

CLIMATIQ_FOOD_ACTIVITY: dict[str, dict[str, Any]] = {
    "carne_rossa": {
        "activity_id": "food-type_beef",
        "region": "FR",
    },
    "pollo": {
        "activity_id": "food-type_chicken",
        "region": "FR",
    },
    "pesce": {
        "activity_id": "food-type_fish_all_species-origin_region_multi_region",
        "region": "GLOBAL",
    },
    "latticini": {
        "activity_id": "food-type_milk_partly_skimmed_1.5_percent_fat",
        "region": "FR",
    },
    "verdure": {
        "activity_id": "food-type_tomato_raw",
        "region": "FR",
    },
    "verdure_fresche": {
        "activity_id": "food-type_carrot_raw",
        "region": "FR",
    },
    "frutta": {
        "activity_id": "food-type_banana_raw",
        "region": "FR",
    },
    "frutta_fresca": {
        "activity_id": "food-type_banana_raw",
        "region": "FR",
    },
    "cereali_pasta": {
        "activity_id": "food-type_pasta_raw",
        "region": "FR",
    },
    "cereali_pasta_riso": {
        "activity_id": "food-type_pasta_raw",
        "region": "FR",
    },
    "bevande": {
        "activity_id": "food-type_cola_with_sugar",
        "region": "FR",
    },
    "snack_dolci": {
        "activity_id": "food-type_chocolate_bitter",
        "region": "FR",
    },
}

CLIMATIQ_CLOTHING_ACTIVITY: dict[str, dict[str, Any]] = {
    "cotone": {
        "activity_id": "textiles-type_cotton_fabric",
        "region": "DE",
    },
    "poliestere": {
        "activity_id": "textiles-type_polyester_textiles",
        "region": "CN",
    },
    "lana": {
        "activity_id": "textiles-type_high_count_pure_wool_fabric",
        "region": "CN",
    },
    "nylon": {
        "activity_id": "textiles-type_polyester_textiles",
        "region": "CN",
    },
    "seta": {
        "activity_id": "textiles-type_silk_fabric",
        "region": "CN",
    },
}


async def estimate_meal_co2(
    items: list[dict[str, Any]],
    climatiq: ClimatiqClient | None,
) -> list[dict[str, Any]]:
    """Estimate CO2 for each meal item identified by Claude.

    Each item: {"name": str, "portion_g": float, "category": str}
    Returns items with added "estimated_co2_kg" field.
    """
    results = []
    for item in items:
        category = item.get("category", "altro")
        portion_kg = item.get("portion_g", 129.0) / 1000.0

        co2_per_kg = await _get_food_co2_per_kg(category, climatiq)
        co2_kg = round(portion_kg * co2_per_kg, 4)

        results.append({
            **item,
            "estimated_co2_kg": co2_kg,
        })
    return results


async def estimate_grocery_co2(
    items: list[dict[str, Any]],
    climatiq: ClimatiqClient | None,
) -> list[dict[str, Any]]:
    """Estimate CO2 for each grocery item identified by Claude.

    Each item: {"name": str, "quantity": int, "weight_kg": float, "category": str}
    Returns items with added "estimated_co2_kg" field.
    """
    results = []
    for item in items:
        category = item.get("category", "altro")
        quantity = item.get("quantity", 1)
        weight_kg = item.get("weight_kg", 0.5)
        total_weight = quantity * weight_kg

        co2_per_kg = await _get_food_co2_per_kg(category, climatiq)
        co2_kg = round(total_weight * co2_per_kg, 4)

        results.append({
            **item,
            "estimated_co2_kg": co2_kg,
        })
    return results


async def estimate_clothing_co2(
    items: list[dict[str, Any]],
    climatiq: ClimatiqClient | None,
) -> list[dict[str, Any]]:
    """Estimate CO2 for each clothing item identified by Claude.

    Each item: {"type": str, "material": str, "brand_guess": str|null, "weight_kg": float}
    Returns items with added "estimated_co2_kg" field.
    """
    results = []
    for item in items:
        material = item.get("material", "misti")
        weight_kg = item.get("weight_kg", 0.5)

        co2_per_kg = await _get_clothing_co2_per_kg(material, climatiq)
        co2_kg = round(weight_kg * co2_per_kg, 4)

        results.append({
            **item,
            "estimated_co2_kg": co2_kg,
        })
    return results


async def _get_food_co2_per_kg(
    category: str,
    climatiq: ClimatiqClient | None,
) -> float:
    """Get CO2 per kg for a food category from Climatiq, fallback to hardcoded."""
    fallback = FOOD_CO2_PER_KG.get(category, FOOD_CO2_PER_KG["altro"])
    mapping = CLIMATIQ_FOOD_ACTIVITY.get(category)

    if climatiq is None or not climatiq.enabled or mapping is None:
        return fallback

    return await climatiq.estimate(
        activity_id=mapping["activity_id"],
        parameters={"weight": 1, "weight_unit": "kg"},
        region=mapping.get("region", "FR"),
        fallback=fallback,
    )


async def _get_clothing_co2_per_kg(
    material: str,
    climatiq: ClimatiqClient | None,
) -> float:
    """Get CO2 per kg for a clothing material from Climatiq, fallback to hardcoded."""
    fallback = CLOTHING_CO2_PER_KG.get(material, CLOTHING_CO2_PER_KG["misti"])
    mapping = CLIMATIQ_CLOTHING_ACTIVITY.get(material)

    if climatiq is None or not climatiq.enabled or mapping is None:
        return fallback

    return await climatiq.estimate(
        activity_id=mapping["activity_id"],
        parameters={"weight": 1, "weight_unit": "kg"},
        region=mapping.get("region", "DE"),
        fallback=fallback,
    )
