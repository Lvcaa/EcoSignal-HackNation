"""Core footprint calculation logic — pure Python, no framework dependencies."""

# TODO: add optional weekly_km override field to FootprintRequest

from app.enums import TransportMode
from app.factors import (
    ASSUMED_WEEKLY_KM,
    EMISSION_FACTOR_BIKE_KM,
    EMISSION_FACTOR_CAR_KM,
    EMISSION_FACTOR_DIET,
    EMISSION_FACTOR_HOME,
    EMISSION_FACTOR_TRANSIT_KM,
    EMISSION_FACTOR_WALK_KM,
    LABEL_THRESHOLD_AVERAGE,
    LABEL_THRESHOLD_HIGH,
    LABEL_THRESHOLD_LOW,
    NATIONAL_AVG_TOTAL_KG_WEEK,
)
from app.schemas import CategoryBreakdown, FootprintRequest, FootprintResult

_TRANSPORT_FACTOR: dict[TransportMode, float] = {
    TransportMode.car: EMISSION_FACTOR_CAR_KM,
    TransportMode.transit: EMISSION_FACTOR_TRANSIT_KM,
    TransportMode.bike: EMISSION_FACTOR_BIKE_KM,
    TransportMode.walk: EMISSION_FACTOR_WALK_KM,
}


def calculate_footprint(request: FootprintRequest) -> FootprintResult:
    """Calculate weekly CO₂ footprint from user habits."""
    # 1. Validate week_start is Monday
    if request.week_start.weekday() != 0:
        raise ValueError("week_start must be a Monday")

    # 2. Transport
    km = ASSUMED_WEEKLY_KM[request.transport_mode]
    if request.transport_mode == TransportMode.mixed:
        factor = 0.5 * EMISSION_FACTOR_CAR_KM + 0.5 * EMISSION_FACTOR_TRANSIT_KM
    else:
        factor = _TRANSPORT_FACTOR[request.transport_mode]
    transport_kg = round(km * factor, 2)

    # 3. Food
    food_kg = round(EMISSION_FACTOR_DIET[request.diet_type], 2)

    # 4. Home
    home_kg = round(request.home_size_sqm * EMISSION_FACTOR_HOME[request.home_type], 2)

    # 5. Total
    total = round(transport_kg + food_kg + home_kg, 2)

    # 6. vs national average
    pct = round(
        (total - NATIONAL_AVG_TOTAL_KG_WEEK) / NATIONAL_AVG_TOTAL_KG_WEEK, 4
    )

    # 7. Label
    ratio = total / NATIONAL_AVG_TOTAL_KG_WEEK
    if ratio < LABEL_THRESHOLD_LOW:
        label = "low"
    elif ratio < LABEL_THRESHOLD_AVERAGE:
        label = "average"
    elif ratio < LABEL_THRESHOLD_HIGH:
        label = "high"
    else:
        label = "very_high"

    # 8. Result
    return FootprintResult(
        user_id=request.user_id,
        week_start=request.week_start,
        total_kg_co2=total,
        breakdown=CategoryBreakdown(
            transport_kg=transport_kg,
            food_kg=food_kg,
            home_kg=home_kg,
        ),
        vs_national_avg_pct=pct,
        label=label,
    )
