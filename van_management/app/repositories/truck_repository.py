from sqlalchemy import func as sa_func
from sqlalchemy.orm import Session

from app.models.truck_state import TruckStateVersion


class TruckRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_max_version(self, truck_id: str) -> int | None:
        return (
            self.db.query(sa_func.max(TruckStateVersion.version))
            .filter(TruckStateVersion.truck_id == truck_id)
            .scalar()
        )

    def create(self, state: TruckStateVersion) -> TruckStateVersion:
        self.db.add(state)
        self.db.commit()
        self.db.refresh(state)
        return state

    def get_history(
        self, truck_id: str, skip: int = 0, limit: int = 50
    ) -> list[TruckStateVersion]:
        return (
            self.db.query(TruckStateVersion)
            .filter(TruckStateVersion.truck_id == truck_id)
            .order_by(TruckStateVersion.version.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_truck(self, truck_id: str) -> int:
        return (
            self.db.query(TruckStateVersion)
            .filter(TruckStateVersion.truck_id == truck_id)
            .count()
        )
