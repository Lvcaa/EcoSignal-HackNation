"""Pydantic schemas for user-profile service — source of truth."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Self
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

# ── Enums ─────────────────────────────────────────────────────

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


# ── Auth schemas ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    display_name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: datetime
    iat: datetime


# ── Profile schemas ───────────────────────────────────────────

class ProfileUpdateRequest(BaseModel):
    zip_code: str | None = Field(None, pattern=r"^\d{5}$")
    transport_mode: TransportMode | None = None
    diet_type: DietType | None = None
    home_type: HomeType | None = None
    home_size_sqm: int | None = Field(None, gt=0, le=1000)
    commute_days_per_week: int | None = Field(None, ge=0, le=7)
    has_pets: bool | None = None
    pet_type: PetType | None = None
    pet_count: int | None = Field(None, ge=0, le=10)

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if all(
            v is None
            for v in [
                self.zip_code,
                self.transport_mode,
                self.diet_type,
                self.home_type,
                self.home_size_sqm,
                self.commute_days_per_week,
                self.has_pets,
                self.pet_type,
                self.pet_count,
            ]
        ):
            msg = "At least one field must be provided"
            raise ValueError(msg)
        return self


class UserProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    email: str
    display_name: str
    zip_code: str | None = None
    transport_mode: TransportMode | None = None
    diet_type: DietType | None = None
    home_type: HomeType | None = None
    home_size_sqm: int | None = None
    commute_days_per_week: int | None = None
    has_pets: bool | None = None
    pet_type: PetType | None = None
    pet_count: int | None = None
    onboarding_complete: bool
    created_at: datetime
    updated_at: datetime


# ── Error schema ──────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
