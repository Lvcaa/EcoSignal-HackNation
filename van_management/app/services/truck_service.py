import logging

from sqlalchemy.orm import Session

from app.models.truck_state import TruckStateVersion
from app.models.truck_state import WasteType as ModelWasteType
from app.repositories.truck_repository import TruckRepository
from app.schemas.truck import TruckUpdateRequest

logger = logging.getLogger(__name__)


class TruckService:
    def __init__(self, db: Session) -> None:
        self.repo = TruckRepository(db)

    def process_update(self, payload: TruckUpdateRequest) -> TruckStateVersion:
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

    def get_history(
        self, truck_id: str, page: int = 1, page_size: int = 50
    ) -> tuple[list[TruckStateVersion], int]:
        total = self.repo.count_by_truck(truck_id)
        if total == 0:
            return [], 0
        skip = (page - 1) * page_size
        records = self.repo.get_history(truck_id, skip=skip, limit=page_size)
        return records, total
