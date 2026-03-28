"""Unit tests for footprint calculation service — pure Python, no HTTP."""

from datetime import date, timedelta
from uuid import UUID

import pytest

from app.enums import DietType, HomeType, TransportMode
from app.factors import (
    ASSUMED_WEEKLY_KM,
    EMISSION_FACTOR_CAR_KM,
    EMISSION_FACTOR_TRANSIT_KM,
)
from app.schemas import FootprintRequest, FootprintResult
from app.service import calculate_footprint

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _next_monday() -> date:
    today = date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        return today
    return today + timedelta(days=days_ahead)


MONDAY = _next_monday()


def _make_request(**overrides: object) -> FootprintRequest:
    defaults: dict[str, object] = {
        "user_id": TEST_USER_ID,
        "transport_mode": TransportMode.car,
        "diet_type": DietType.meat_weekly,
        "home_type": HomeType.apartment,
        "home_size_sqm": 70,
        "week_start": MONDAY,
    }
    defaults.update(overrides)
    return FootprintRequest(**defaults)


# ── Happy path: all transport modes ────────────────────────────


@pytest.mark.parametrize(
    "mode",
    list(TransportMode),
)
def test_happy_path_returns_result(mode: TransportMode) -> None:
    req = _make_request(transport_mode=mode)
    result = calculate_footprint(req)
    assert isinstance(result, FootprintResult)
    assert result.total_kg_co2 > 0


@pytest.mark.parametrize(
    "mode",
    list(TransportMode),
)
def test_breakdown_sums_to_total(mode: TransportMode) -> None:
    req = _make_request(transport_mode=mode)
    result = calculate_footprint(req)
    breakdown_sum = (
        result.breakdown.transport_kg + result.breakdown.food_kg + result.breakdown.home_kg
    )
    assert abs(breakdown_sum - result.total_kg_co2) < 0.01


@pytest.mark.parametrize(
    "mode",
    list(TransportMode),
)
def test_vs_national_avg_is_float(mode: TransportMode) -> None:
    req = _make_request(transport_mode=mode)
    result = calculate_footprint(req)
    assert isinstance(result.vs_national_avg_pct, float)


# ── Label assignment ───────────────────────────────────────────


def test_label_low() -> None:
    """Vegan cyclist in a small apartment → low."""
    req = _make_request(
        transport_mode=TransportMode.bike,
        diet_type=DietType.vegan,
        home_type=HomeType.apartment,
        home_size_sqm=30,
    )
    result = calculate_footprint(req)
    assert result.label == "low"


def test_label_very_high() -> None:
    """Car + meat_daily + large house → very_high."""
    req = _make_request(
        transport_mode=TransportMode.car,
        diet_type=DietType.meat_daily,
        home_type=HomeType.house,
        home_size_sqm=200,
    )
    result = calculate_footprint(req)
    assert result.label == "very_high"


def test_label_average() -> None:
    """Profile close to national average → average."""
    req = _make_request(
        transport_mode=TransportMode.transit,
        diet_type=DietType.meat_weekly,
        home_type=HomeType.house,
        home_size_sqm=80,
    )
    result = calculate_footprint(req)
    assert result.label == "average"


# ── Mixed transport ────────────────────────────────────────────


def test_mixed_uses_blended_factor() -> None:
    req = _make_request(transport_mode=TransportMode.mixed)
    result = calculate_footprint(req)
    km = ASSUMED_WEEKLY_KM[TransportMode.mixed]
    expected_factor = 0.5 * EMISSION_FACTOR_CAR_KM + 0.5 * EMISSION_FACTOR_TRANSIT_KM
    expected_transport = round(km * expected_factor, 2)
    assert result.breakdown.transport_kg == expected_transport


# ── Rounding ───────────────────────────────────────────────────


def test_all_floats_have_at_most_two_decimals() -> None:
    req = _make_request()
    result = calculate_footprint(req)
    for val in [
        result.total_kg_co2,
        result.breakdown.transport_kg,
        result.breakdown.food_kg,
        result.breakdown.home_kg,
    ]:
        assert round(val, 2) == val


# ── Week start validation ──────────────────────────────────────


def test_monday_no_error() -> None:
    req = _make_request(week_start=MONDAY)
    result = calculate_footprint(req)
    assert result.week_start == MONDAY


def test_tuesday_raises() -> None:
    tuesday = MONDAY + timedelta(days=1)
    req = _make_request(week_start=tuesday)
    with pytest.raises(ValueError, match="week_start must be a Monday"):
        calculate_footprint(req)


def test_sunday_raises() -> None:
    sunday = MONDAY + timedelta(days=6)
    req = _make_request(week_start=sunday)
    with pytest.raises(ValueError, match="week_start must be a Monday"):
        calculate_footprint(req)


# ── vs_national_avg_pct sign ──────────────────────────────────


def test_low_profile_negative_pct() -> None:
    req = _make_request(
        transport_mode=TransportMode.bike,
        diet_type=DietType.vegan,
        home_type=HomeType.apartment,
        home_size_sqm=30,
    )
    result = calculate_footprint(req)
    assert result.vs_national_avg_pct < 0


def test_high_profile_positive_pct() -> None:
    req = _make_request(
        transport_mode=TransportMode.car,
        diet_type=DietType.meat_daily,
        home_type=HomeType.house,
        home_size_sqm=200,
    )
    result = calculate_footprint(req)
    assert result.vs_national_avg_pct > 0


# ── Breakdown sum parametrized across diets × home types ──────


@pytest.mark.parametrize("diet", list(DietType))
@pytest.mark.parametrize("home", list(HomeType))
def test_breakdown_sum_all_combos(diet: DietType, home: HomeType) -> None:
    req = _make_request(diet_type=diet, home_type=home)
    result = calculate_footprint(req)
    breakdown_sum = (
        result.breakdown.transport_kg + result.breakdown.food_kg + result.breakdown.home_kg
    )
    assert abs(breakdown_sum - result.total_kg_co2) < 0.01
