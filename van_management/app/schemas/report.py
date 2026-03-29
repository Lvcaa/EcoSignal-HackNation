from datetime import datetime

from pydantic import BaseModel, Field


class ReportOut(BaseModel):
    id: str
    userId: str = Field(validation_alias="user_id")
    binId: str = Field(validation_alias="bin_id")
    lat: float
    lng: float
    address: str
    photo: str
    status: str
    xp: int
    createdAt: datetime = Field(validation_alias="created_at")

    model_config = {"populate_by_name": True, "from_attributes": True}
