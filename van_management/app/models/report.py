import enum

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class ReportStatus(str, enum.Enum):
    SENT = "sent"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), nullable=False)
    bin_id: Mapped[str] = mapped_column(String(50), nullable=False)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    photo: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        default=ReportStatus.SENT,
    )
    xp: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Report id={self.id} bin={self.bin_id} status={self.status.value}>"
