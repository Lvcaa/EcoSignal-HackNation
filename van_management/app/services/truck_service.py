import logging

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.truck_state import TruckStateVersion
from app.models.truck_state import WasteType as ModelWasteType
from app.repositories.truck_repository import TruckRepository
from app.schemas.truck import TruckBatchUpdateRequest, TruckUpdateRequest

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3


class TruckService:
    def __init__(self, db: Session) -> None:
        self.repo = TruckRepository(db)

    def process_update(self, payload: TruckUpdateRequest) -> TruckStateVersion:
        # Retry loop: concurrent workers can race on the unique (truck_id, version)
        # constraint.  On IntegrityError we roll back and re-read the real max version
        # before retrying.  Three attempts cover any realistic burst.
        for attempt in range(_MAX_RETRIES):
            try:
                max_version = self.repo.get_max_version(payload.truck_id)
                new_version = (max_version or 0) + 1
                state = TruckStateVersion(
                    truck_id=payload.truck_id,
                    waste_type=ModelWasteType(payload.waste_type.value),
                    latitude=payload.current_position.latitude,
                    longitude=payload.current_position.longitude,
                    position_timestamp=payload.current_position.timestamp,
                    version=new_version,
                )
                created = self.repo.create(state)
                logger.info("Truck %s updated to version %d", payload.truck_id, new_version)
                return created
            except IntegrityError:
                self.repo.db.rollback()
                if attempt == _MAX_RETRIES - 1:
                    logger.warning(
                        "Truck %s: version conflict unresolved after %d retries",
                        payload.truck_id,
                        _MAX_RETRIES,
                    )
                    raise
                logger.debug(
                    "Truck %s: version conflict on attempt %d, retrying",
                    payload.truck_id,
                    attempt + 1,
                )
        raise RuntimeError("unreachable")

    def get_history(
        self, truck_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[TruckStateVersion], int]:
        total = self.repo.count_by_truck(truck_id)
        if total == 0:
            return [], 0
        skip = (page - 1) * page_size
        records = self.repo.get_history(truck_id, skip=skip, limit=page_size)
        return records, total

    def get_latest(self, truck_id: str) -> TruckStateVersion | None:
        return self.repo.get_latest(truck_id)

    def get_fleet_latest(self) -> list[TruckStateVersion]:
        return self.repo.get_fleet_latest()

    def process_batch(self, payload: TruckBatchUpdateRequest) -> list[TruckStateVersion]:
        # 1. Fetch current max versions for all distinct truck_ids — one query.
        distinct_ids = list({u.truck_id for u in payload.updates})
        max_versions = self.repo.get_max_versions_bulk(distinct_ids)

        # 2. Build all ORM objects, using a local counter so that if the same
        #    truck_id appears more than once in the batch the versions stack
        #    correctly within the batch itself.
        local: dict[str, int] = {}
        states: list[TruckStateVersion] = []
        for update in payload.updates:
            base = local.get(update.truck_id, max_versions.get(update.truck_id, 0))
            new_version = base + 1
            local[update.truck_id] = new_version
            states.append(
                TruckStateVersion(
                    truck_id=update.truck_id,
                    company_id=payload.company_id,
                    waste_type=ModelWasteType(update.waste_type.value),
                    latitude=update.current_position.latitude,
                    longitude=update.current_position.longitude,
                    position_timestamp=update.current_position.timestamp,
                    version=new_version,
                )
            )

        # 3. Single-commit insert — retry the whole build+insert on conflict.
        for attempt in range(_MAX_RETRIES):
            try:
                created = self.repo.create_bulk(states)
                logger.info(
                    "Batch from '%s': %d update(s) stored", payload.company_id, len(created)
                )
                return created
            except IntegrityError:
                self.repo.db.rollback()
                if attempt == _MAX_RETRIES - 1:
                    raise
                # Re-read max versions so the next attempt picks up the latest state.
                max_versions = self.repo.get_max_versions_bulk(distinct_ids)
                local = {}
                states = []
                for update in payload.updates:
                    base = local.get(update.truck_id, max_versions.get(update.truck_id, 0))
                    new_version = base + 1
                    local[update.truck_id] = new_version
                    states.append(
                        TruckStateVersion(
                            truck_id=update.truck_id,
                            company_id=payload.company_id,
                            waste_type=ModelWasteType(update.waste_type.value),
                            latitude=update.current_position.latitude,
                            longitude=update.current_position.longitude,
                            position_timestamp=update.current_position.timestamp,
                            version=new_version,
                        )
                    )
        raise RuntimeError("unreachable")
