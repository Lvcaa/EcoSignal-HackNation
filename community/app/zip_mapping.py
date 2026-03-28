"""Duplicated ZIP-to-city mapping for community service (no cross-service imports)."""

from __future__ import annotations

ZIP_CITY_MAP: dict[str, str] = {
    "00100": "Roma",
    "20100": "Milano",
    "25100": "Brescia",
    "24100": "Bergamo",
    "80100": "Napoli",
    "84100": "Salerno",
    "90100": "Palermo",
    "95100": "Catania",
    "30100": "Venezia",
    "37100": "Verona",
    "35100": "Padova",
    "10100": "Torino",
    "40100": "Bologna",
    "43100": "Parma",
    "70100": "Bari",
    "50100": "Firenze",
    "56100": "Pisa",
    "88100": "Catanzaro",
    "89100": "Reggio Calabria",
    "09100": "Cagliari",
    "16100": "Genova",
    "60100": "Ancona",
    "67100": "L'Aquila",
    "65100": "Pescara",
    "38100": "Trento",
    "39100": "Bolzano",
    "34100": "Trieste",
    "06100": "Perugia",
    "85100": "Potenza",
    "86100": "Campobasso",
    "11100": "Aosta",
}


def get_city(zip_code: str) -> str | None:
    """Look up city name for a ZIP code, or None if unknown."""
    return ZIP_CITY_MAP.get(zip_code)
