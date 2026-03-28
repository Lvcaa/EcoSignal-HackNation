import enum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SignalType(str, enum.Enum):
    EMERGENZA = "emergenza"
    INFO = "info"


class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    signal_type: Mapped[SignalType] = mapped_column(
        Enum(SignalType, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attachments: Mapped[list["SignalAttachment"]] = relationship(
        "SignalAttachment", back_populates="signal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_signals_signal_type", "signal_type"),
        Index("ix_signals_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Signal id={self.id} type={self.signal_type.value} title={self.title!r}>"


class SignalAttachment(Base):
    __tablename__ = "signal_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    signal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    signal: Mapped["Signal"] = relationship("Signal", back_populates="attachments")

    def __repr__(self) -> str:
        return f"<SignalAttachment id={self.id} signal_id={self.signal_id} file={self.original_filename!r}>"
