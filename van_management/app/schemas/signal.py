from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SignalType(str, Enum):
    emergenza = "emergenza"
    info = "info"


class SignalCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=5000)
    signal_type: SignalType
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Incendio boschivo",
                    "description": "Fumo visibile dalla strada provinciale SP45, lato nord",
                    "signal_type": "emergenza",
                    "latitude": 45.4642,
                    "longitude": 9.1900,
                }
            ]
        }
    }


class AttachmentOut(BaseModel):
    id: int
    signal_id: int
    original_filename: str
    content_type: str
    file_size: int
    created_at: datetime


class SignalOut(BaseModel):
    id: int
    title: str
    description: str
    signal_type: str
    latitude: float
    longitude: float
    created_at: datetime
    attachments: list[AttachmentOut] = Field(default_factory=list)


class SignalListOut(BaseModel):
    total: int
    page: int
    page_size: int
    signals: list[SignalOut]
