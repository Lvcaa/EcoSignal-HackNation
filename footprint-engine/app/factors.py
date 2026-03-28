"""Emission factors for Italian carbon footprint calculation.

All values are in kg CO₂-equivalent unless otherwise noted.
Sources are cited inline on every constant.
"""

from app.enums import DietType, HomeType, TransportMode

# ── Transport (kg CO₂e per passenger-km) ────────────────────────

# Average Italian petrol car, 1.4 occupancy factor
# Source: ISPRA — Fattori di emissione per il trasporto stradale 2023, Table 7
EMISSION_FACTOR_CAR_KM: float = 0.170

# Urban public transport weighted mix (60% bus + 40% metro/tram)
# Source: ISPRA — Trasporto pubblico locale 2023; DEFRA 2023 Table "Bus" + "Rail"
EMISSION_FACTOR_TRANSIT_KM: float = 0.065

# Cycling — zero direct emissions, negligible lifecycle (~0.005 for manufacturing)
# Source: IPCC AR6 WGIII Ch. 10, Table 10.4 (active transport ≈ 0)
EMISSION_FACTOR_BIKE_KM: float = 0.005

# Walking — zero emissions
# Source: IPCC AR6 WGIII Ch. 10
EMISSION_FACTOR_WALK_KM: float = 0.0


# ── Assumed weekly km by transport mode ──────────────────────────
# Average Italian urban commuter distances, rounded to weekly totals.
# Source: ISTAT — Mobilità urbana 2022, Table 3.2; ISFORT 18° Rapporto 2022

ASSUMED_WEEKLY_KM: dict[TransportMode, float] = {
    TransportMode.car: 150.0,       # ~30 km/day × 5 workdays
    TransportMode.transit: 80.0,    # ~16 km/day × 5 workdays
    TransportMode.bike: 30.0,       # ~6 km/day × 5 workdays
    TransportMode.walk: 10.0,       # ~2 km/day × 5 workdays
    TransportMode.mixed: 110.0,     # weighted avg: 0.5 × car + 0.5 × transit
}


# ── Food (kg CO₂e per person per week) ──────────────────────────
# Based on lifecycle analysis of Italian dietary patterns.
# Source: Poore & Nemecek 2018 (Science 360:987-992), adapted for
# Italian portion sizes per INRAN Linee Guida 2018.
# Cross-checked with Scarborough et al. 2023 (Nature Food 4:565-574).

EMISSION_FACTOR_DIET: dict[DietType, float] = {
    DietType.meat_daily: 38.0,      # high-meat Western diet, ~5.4 kg CO₂e/day
    DietType.meat_weekly: 24.5,     # Mediterranean diet, meat 2-3×/week
    DietType.vegetarian: 16.5,      # lacto-ovo vegetarian, dairy/eggs included
    DietType.vegan: 10.5,           # plant-based only
}


# ── Home energy (kg CO₂e per m² per week) ───────────────────────
# Derived from annual residential energy intensity converted to weekly.
# Includes heating, cooling, hot water, cooking, appliances.
# Source: ISPRA — Inventario nazionale emissioni gas serra 2023,
# Settore residenziale, Table 3.14; ENEA — Rapporto annuale
# efficienza energetica 2023.
# Italy avg residential: ~25 kg CO₂/m²/year → ~0.48 kg/m²/week
# Apartments benefit from shared walls → ~20% lower than detached.

EMISSION_FACTOR_HOME: dict[HomeType, float] = {
    HomeType.apartment: 0.38,       # multi-family, shared walls, better insulation
    HomeType.house: 0.55,           # detached/semi-detached, higher heating load
}


# ── National averages (kg CO₂e per capita per week) ─────────────
# Used to compute vs_national_avg_pct in the footprint result.
# Derived from ISPRA national inventory 2023, per-capita annual totals
# divided by 52 weeks, scoped to the three categories we track.

# Transport: ~1.8 t CO₂/capita/year → ~34.6 kg/week
# Source: ISPRA — Emissioni da trasporto 2023, per-capita allocation
NATIONAL_AVG_TRANSPORT_KG_WEEK: float = 34.6

# Food: ~1.4 t CO₂/capita/year → ~26.9 kg/week
# Source: ISPRA/CREA — Emissioni dal sistema alimentare 2023
NATIONAL_AVG_FOOD_KG_WEEK: float = 26.9

# Residential: ~1.1 t CO₂/capita/year → ~21.2 kg/week
# Source: ISPRA — Emissioni settore residenziale 2023
NATIONAL_AVG_HOME_KG_WEEK: float = 21.2

# Total national average across tracked categories
NATIONAL_AVG_TOTAL_KG_WEEK: float = (
    NATIONAL_AVG_TRANSPORT_KG_WEEK
    + NATIONAL_AVG_FOOD_KG_WEEK
    + NATIONAL_AVG_HOME_KG_WEEK
)  # = 82.7 kg CO₂e/week


# ── Label thresholds (ratio of total vs national average) ───────
# Used in service.py to assign a human-readable label.

LABEL_THRESHOLD_LOW: float = 0.60
LABEL_THRESHOLD_AVERAGE: float = 1.10
LABEL_THRESHOLD_HIGH: float = 1.50
