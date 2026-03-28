from collections.abc import Iterable
from math import asin, cos, radians, sin, sqrt
from typing import TypeVar

T = TypeVar("T")

EARTH_RADIUS_KM = 6371.0088


def haversine_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    lat1 = radians(latitude_a)
    lon1 = radians(longitude_a)
    lat2 = radians(latitude_b)
    lon2 = radians(longitude_b)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    arc = (
        sin(dlat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * asin(sqrt(arc))


def pairwise(items: Iterable[T]) -> list[tuple[T, T]]:
    materialized = list(items)
    return list(zip(materialized, materialized[1:]))


def round_kg(value: float) -> float:
    return round(value, 6)

