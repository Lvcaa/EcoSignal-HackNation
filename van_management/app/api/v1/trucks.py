from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.truck import TruckHistoryOut, TruckStateOut, TruckUpdateRequest
from app.services.truck_service import TruckService

router = APIRouter(prefix="/api/v1/trucks", tags=["trucks"])


@router.post("/update", response_model=ApiResponse, status_code=201)
def update_truck(
    payload: TruckUpdateRequest, db: Session = Depends(get_db)
) -> ApiResponse:
    service = TruckService(db)
    state = service.process_update(payload)
    return ApiResponse(
        success=True,
        message=f"Truck {state.truck_id} updated to version {state.version}",
        data=TruckStateOut(
            id=state.id,
            truck_id=state.truck_id,
            waste_type=state.waste_type.value,
            latitude=state.latitude,
            longitude=state.longitude,
            position_timestamp=state.position_timestamp,
            version=state.version,
            created_at=state.created_at,
        ).model_dump(mode="json"),
    )


@router.get("/{truck_id}/history", response_model=ApiResponse)
def get_truck_history(
    truck_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = TruckService(db)
    records, total = service.get_history(truck_id, page=page, page_size=page_size)

    if total == 0:
        raise HTTPException(
            status_code=404, detail=f"No history found for truck '{truck_id}'"
        )

    return ApiResponse(
        success=True,
        message=f"Found {total} record(s) for truck '{truck_id}'",
        data=TruckHistoryOut(
            truck_id=truck_id,
            total=total,
            page=page,
            page_size=page_size,
            records=[
                TruckStateOut(
                    id=r.id,
                    truck_id=r.truck_id,
                    waste_type=r.waste_type.value,
                    latitude=r.latitude,
                    longitude=r.longitude,
                    position_timestamp=r.position_timestamp,
                    version=r.version,
                    created_at=r.created_at,
                )
                for r in records
            ],
        ).model_dump(mode="json"),
    )
