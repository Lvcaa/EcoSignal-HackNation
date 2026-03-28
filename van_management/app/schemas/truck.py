from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class WasteType(str, Enum):
    organic = "organic"
    paper = "paper"
    plastic = "plastic"
    glass = "glass"
    mixed = "mixed"


class Position(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    timestamp: datetime


class TruckUpdateRequest(BaseModel):
    truck_id: str = Field(..., min_length=1, max_length=64)
    waste_type: WasteType
    current_position: Position

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "truck_id": "TRUCK_001",
                    "waste_type": "organic",
                    "current_position": {
                        "latitude": 45.4642,
                        "longitude": 9.1900,
                        "timestamp": "2026-03-28T10:15:00Z",
                    },
                }
            ]
        }
    }


class TruckStateOut(BaseModel):
    id: int
    truck_id: str
    waste_type: str
    latitude: float
    longitude: float
    position_timestamp: datetime
    version: int
    created_at: datetime


class TruckHistoryOut(BaseModel):
    truck_id: str
    total: int
    page: int
    page_size: int
    records: list[TruckStateOut]
