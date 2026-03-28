from sqlalchemy.orm import Session

from app.models.signal import Signal, SignalAttachment


class SignalRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, signal: Signal) -> Signal:
        self.db.add(signal)
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def get_by_id(self, signal_id: int) -> Signal | None:
        return self.db.query(Signal).filter(Signal.id == signal_id).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> list[Signal]:
        return (
            self.db.query(Signal)
            .order_by(Signal.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        return self.db.query(Signal).count()

    def delete(self, signal: Signal) -> None:
        self.db.delete(signal)
        self.db.commit()

    def create_attachments_bulk(
        self, attachments: list[SignalAttachment]
    ) -> list[SignalAttachment]:
        self.db.add_all(attachments)
        self.db.commit()
        for a in attachments:
            self.db.refresh(a)
        return attachments

    def get_attachment_by_id(
        self, signal_id: int, attachment_id: int
    ) -> SignalAttachment | None:
        return (
            self.db.query(SignalAttachment)
            .filter(
                SignalAttachment.signal_id == signal_id,
                SignalAttachment.id == attachment_id,
            )
            .first()
        )
