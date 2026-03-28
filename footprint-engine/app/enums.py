"""Shared enums for footprint-engine — mirrors user-profile enums."""

from enum import StrEnum


class TransportMode(StrEnum):
    car = "car"
    transit = "transit"
    bike = "bike"
    walk = "walk"
    mixed = "mixed"


class DietType(StrEnum):
    meat_daily = "meat_daily"
    meat_weekly = "meat_weekly"
    vegetarian = "vegetarian"
    vegan = "vegan"


class HomeType(StrEnum):
    apartment = "apartment"
    house = "house"


class PetType(StrEnum):
    dog = "dog"
    cat = "cat"
    small_animal = "small_animal"
    none = "none"
