from sqlalchemy import func as sa_func, select
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

    def get_latest(self, truck_id: str) -> TruckStateVersion | None:
        return (
            self.db.query(TruckStateVersion)
            .filter(TruckStateVersion.truck_id == truck_id)
            .order_by(TruckStateVersion.version.desc())
            .first()
        )

    def get_max_versions_bulk(self, truck_ids: list[str]) -> dict[str, int]:
        """Single GROUP BY query returning {truck_id: max_version} for all requested IDs."""
        rows = (
            self.db.query(
                TruckStateVersion.truck_id,
                sa_func.max(TruckStateVersion.version).label("max_ver"),
            )
            .filter(TruckStateVersion.truck_id.in_(truck_ids))
            .group_by(TruckStateVersion.truck_id)
            .all()
        )
        return {row.truck_id: row.max_ver for row in rows}

    def create_bulk(self, states: list[TruckStateVersion]) -> list[TruckStateVersion]:
        """Insert all rows in a single transaction."""
        self.db.add_all(states)
        self.db.commit()
        for s in states:
            self.db.refresh(s)
        return states

    def get_fleet_latest(self) -> list[TruckStateVersion]:
        """Single JOIN query: latest version row per truck_id.

        Uses a subquery that groups by truck_id and picks MAX(version),
        then joins back to the full table to fetch complete rows.
        This is O(n_trucks) and hits the composite index on (truck_id, version).
        """
        subq = (
            select(
                TruckStateVersion.truck_id,
                sa_func.max(TruckStateVersion.version).label("max_version"),
            )
            .group_by(TruckStateVersion.truck_id)
            .subquery()
        )
        return (
            self.db.query(TruckStateVersion)
            .join(
                subq,
                (TruckStateVersion.truck_id == subq.c.truck_id)
                & (TruckStateVersion.version == subq.c.max_version),
            )
            .order_by(TruckStateVersion.truck_id)
            .all()
        )

    def count_by_truck(self, truck_id: str) -> int:
        return (
            self.db.query(TruckStateVersion)
            .filter(TruckStateVersion.truck_id == truck_id)
            .count()
        )
