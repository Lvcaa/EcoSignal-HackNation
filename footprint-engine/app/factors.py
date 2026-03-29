"""Emission factors for Italian carbon footprint calculation.

All values are in kg CO2-equivalent unless otherwise noted.
Sources are cited inline on every constant.

Factors are loaded from Climatiq API at startup when available,
falling back to hardcoded ISPRA 2023 values.
"""

from __future__ import annotations

import logging

from app.enums import DietType, HomeType, PetType, TransportMode

logger = logging.getLogger(__name__)

# ── Fallback constants (ISPRA 2023 / academic sources) ─────────

# Transport (kg CO2e per passenger-km)
# Source: ISPRA — Fattori di emissione per il trasporto stradale 2023, Table 7
FALLBACK_CAR_KM: float = 0.170
# Source: ISPRA — Trasporto pubblico locale 2023; DEFRA 2023 Table "Bus" + "Rail"
FALLBACK_TRANSIT_KM: float = 0.065
# Source: IPCC AR6 WGIII Ch. 10, Table 10.4
FALLBACK_BIKE_KM: float = 0.005
FALLBACK_WALK_KM: float = 0.0

# Food (kg CO2e per person per week)
# Source: Poore & Nemecek 2018, adapted for Italian portions per INRAN 2018
FALLBACK_DIET: dict[DietType, float] = {
    DietType.meat_daily: 38.0,
    DietType.meat_weekly: 24.5,
    DietType.vegetarian: 16.5,
    DietType.vegan: 10.5,
}

# Home energy (kg CO2e per m2 per week)
# Source: ISPRA — Inventario nazionale emissioni gas serra 2023
FALLBACK_HOME: dict[HomeType, float] = {
    HomeType.apartment: 0.38,
    HomeType.house: 0.55,
}

# Pets (kg CO2e per animal per week)
# Source: Gregory Okin, UCLA 2017 (PLOS ONE 12(8): e0181301)
FALLBACK_PET_WEEKLY: dict[PetType, float] = {
    PetType.dog: 4.2,
    PetType.cat: 2.1,
    PetType.small_animal: 0.5,
    PetType.none: 0.0,
}

# Assumed weekly km by transport mode
# Source: ISTAT — Mobilita urbana 2022, Table 3.2; ISFORT 18 Rapporto 2022
ASSUMED_WEEKLY_KM: dict[TransportMode, float] = {
    TransportMode.car: 150.0,
    TransportMode.transit: 80.0,
    TransportMode.bike: 30.0,
    TransportMode.walk: 10.0,
    TransportMode.mixed: 110.0,
}

# National averages (kg CO2e per capita per week)
# Source: ISPRA national inventory 2023
NATIONAL_AVG_TRANSPORT_KG_WEEK: float = 34.6
NATIONAL_AVG_FOOD_KG_WEEK: float = 26.9
NATIONAL_AVG_HOME_KG_WEEK: float = 21.2
NATIONAL_AVG_TOTAL_KG_WEEK: float = (
    NATIONAL_AVG_TRANSPORT_KG_WEEK
    + NATIONAL_AVG_FOOD_KG_WEEK
    + NATIONAL_AVG_HOME_KG_WEEK
)

# Label thresholds (ratio of total vs national average)
LABEL_THRESHOLD_LOW: float = 0.60
LABEL_THRESHOLD_AVERAGE: float = 1.10
LABEL_THRESHOLD_HIGH: float = 1.50

# Appliance factors (duplicated here for reference, primary in actions-engine)
WASHING_MACHINE_PER_CYCLE_KG: dict[str, float] = {
    "cold": 0.3,
    "warm": 0.6,
    "hot": 1.0,
    "very_hot": 1.5,
}

DISHWASHER_PER_CYCLE_KG: dict[str, float] = {
    "eco": 0.4,
    "normal": 0.7,
    "intensive": 1.1,
}

DRYER_PER_CYCLE_KG: float = 2.0


# ── Climatiq activity ID mapping ───────────────────────────────

CLIMATIQ_TRANSPORT_IDS: dict[str, dict] = {
    "car": {
        "activity_id": "passenger_vehicle-vehicle_type_car-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na",
        "parameters": {"passengers": 1, "distance": 1, "distance_unit": "km"},
    },
    "transit": {
        "activity_id": "passenger_train-route_type_light_rail-fuel_source_na",
        "parameters": {"passengers": 1, "distance": 1, "distance_unit": "km"},
    },
    "bike": {
        "activity_id": "passenger_vehicle-vehicle_type_bicycle-fuel_source_na",
        "parameters": {"distance": 1, "distance_unit": "km"},
    },
}

# Italian electricity grid factor: ~0.25 kg CO2/kWh (ISPRA 2023)
FALLBACK_GRID_FACTOR_KG_PER_KWH: float = 0.25

# Home energy intensity assumptions (kWh per m2 per week)
# Apartment: ~0.38/0.25 = 1.52 kWh/m2/week
# House: ~0.55/0.25 = 2.20 kWh/m2/week
HOME_KWH_PER_SQM_WEEK: dict[HomeType, float] = {
    HomeType.apartment: 1.52,
    HomeType.house: 2.20,
}


# ── Mutable factors dict (populated at startup) ────────────────

FACTORS: dict[str, float] = {
    "car_km": FALLBACK_CAR_KM,
    "transit_km": FALLBACK_TRANSIT_KM,
    "bike_km": FALLBACK_BIKE_KM,
    "walk_km": FALLBACK_WALK_KM,
    "grid_factor": FALLBACK_GRID_FACTOR_KG_PER_KWH,
}


async def load_factors(climatiq_client) -> None:
    """Fetch emission factors from Climatiq and populate FACTORS dict.

    Falls back to hardcoded ISPRA values for any factor that fails.
    """
    if not climatiq_client.enabled:
        logger.info("Climatiq disabled, using ISPRA 2023 fallback factors")
        return

    logger.info("Loading emission factors from Climatiq...")

    # Transport factors (per 1 km)
    transport_fallbacks = {
        "car": FALLBACK_CAR_KM,
        "transit": FALLBACK_TRANSIT_KM,
        "bike": FALLBACK_BIKE_KM,
    }

    for mode, mapping in CLIMATIQ_TRANSPORT_IDS.items():
        co2e = await climatiq_client.estimate(
            activity_id=mapping["activity_id"],
            parameters=mapping["parameters"],
            region="IT",
            fallback=transport_fallbacks[mode],
        )
        FACTORS[f"{mode}_km"] = co2e

    # Grid electricity factor (1 kWh -> kg CO2)
    grid_co2 = await climatiq_client.estimate_electricity(
        energy_kwh=1.0,
        region="IT",
        fallback=FALLBACK_GRID_FACTOR_KG_PER_KWH,
    )
    FACTORS["grid_factor"] = grid_co2

    # Recompute home factors using Climatiq grid factor
    for home_type in HomeType:
        kwh_per_sqm_week = HOME_KWH_PER_SQM_WEEK[home_type]
        FALLBACK_HOME[home_type] = round(kwh_per_sqm_week * grid_co2, 4)

    logger.info("Climatiq factors loaded: %s", FACTORS)


# ── Legacy aliases (used by service.py and tests) ──────────────
# These point to the same mutable dicts / FACTORS dict values.
# After load_factors() runs, FACTORS dict and FALLBACK_HOME are updated in-place.

EMISSION_FACTOR_CAR_KM: float = FALLBACK_CAR_KM
EMISSION_FACTOR_TRANSIT_KM: float = FALLBACK_TRANSIT_KM
EMISSION_FACTOR_BIKE_KM: float = FALLBACK_BIKE_KM
EMISSION_FACTOR_WALK_KM: float = FALLBACK_WALK_KM
EMISSION_FACTOR_DIET = FALLBACK_DIET
EMISSION_FACTOR_HOME = FALLBACK_HOME
EMISSION_FACTOR_PET_WEEKLY = FALLBACK_PET_WEEKLY
