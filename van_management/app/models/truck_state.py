import enum

from sqlalchemy import DateTime, Enum, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class WasteType(str, enum.Enum):
    ORGANIC = "organic"
    PAPER = "paper"
    PLASTIC = "plastic"
    GLASS = "glass"
    MIXED = "mixed"


class TruckStateVersion(Base):
    __tablename__ = "truck_state_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    truck_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    company_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    waste_type: Mapped[WasteType] = mapped_column(
        Enum(WasteType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    position_timestamp: Mapped[str] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("truck_id", "version", name="uq_truck_version"),
        Index("ix_truck_version", "truck_id", "version"),
        Index("ix_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<TruckStateVersion truck_id={self.truck_id} v={self.version}>"
