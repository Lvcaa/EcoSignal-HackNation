"""EcoSignal Image Analyzer — request/response schemas."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Union

from pydantic import BaseModel


class AnalysisType(str, Enum):
    meal = "meal"
    grocery = "grocery"
    clothing = "clothing"


class Confidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


# ── Request ───────────────────────────────────────────────

class ImageAnalysisRequest(BaseModel):
    image_base64: Optional[str] = None
    analysis_type: AnalysisType
    user_description: Optional[str] = None


# ── Meal ──────────────────────────────────────────────────

class MealItem(BaseModel):
    name: str
    portion_g: float
    estimated_co2_kg: float


class MealAnalysisResult(BaseModel):
    items: list[MealItem]
    total_co2_kg: float
    confidence: Confidence


# ── Grocery ───────────────────────────────────────────────

class GroceryItem(BaseModel):
    name: str
    quantity: int
    category: str
    estimated_co2_kg: float


class GroceryAnalysisResult(BaseModel):
    items: list[GroceryItem]
    total_co2_kg: float
    confidence: Confidence


# ── Clothing ──────────────────────────────────────────────

class ClothingItem(BaseModel):
    name: str = ""
    type: str
    material: str
    brand_guess: Optional[str] = None
    estimated_co2_kg: float


class ClothingAnalysisResult(BaseModel):
    items: list[ClothingItem]
    total_co2_kg: float
    confidence: Confidence


# ── Response ──────────────────────────────────────────────

class ImageAnalysisResponse(BaseModel):
    analysis_type: AnalysisType
    result: Union[MealAnalysisResult, GroceryAnalysisResult, ClothingAnalysisResult]
    analyzed_at: datetime
    is_fallback: bool


# ── Error ─────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
