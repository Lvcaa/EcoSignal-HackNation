from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.truck import (
    BatchUpdateOut,
    TruckBatchUpdateRequest,
    TruckHistoryOut,
    TruckStateOut,
    TruckUpdateRequest,
)
from app.services.truck_service import TruckService

router = APIRouter(prefix="/api/v1/trucks", tags=["trucks"])


@router.post(
    "/update",
    response_model=ApiResponse,
    status_code=201,
    summary="Create a new truck state version",
    description=(
        "Ingest a new telemetry update for a truck. Each request creates a new "
        "immutable versioned record."
    ),
)
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


@router.post(
    "/batch",
    response_model=ApiResponse,
    status_code=201,
    summary="Ingest a batch of truck state updates from a company",
    description=(
        "Accepts up to 500 truck updates in a single request. "
        "All rows are written in one transaction. "
        "Version counters are incremented correctly even when the same "
        "truck_id appears more than once within the batch."
    ),
)
def batch_update_trucks(
    payload: TruckBatchUpdateRequest, db: Session = Depends(get_db)
) -> ApiResponse:
    service = TruckService(db)
    states = service.process_batch(payload)
    return ApiResponse(
        success=True,
        message=f"Accepted {len(states)} update(s) from '{payload.company_id}'",
        data=BatchUpdateOut(
            company_id=payload.company_id,
            accepted=len(states),
            records=[
                TruckStateOut(
                    id=s.id,
                    truck_id=s.truck_id,
                    company_id=s.company_id,
                    waste_type=s.waste_type.value,
                    latitude=s.latitude,
                    longitude=s.longitude,
                    position_timestamp=s.position_timestamp,
                    version=s.version,
                    created_at=s.created_at,
                )
                for s in states
            ],
        ).model_dump(mode="json"),
    )


@router.get(
    "",
    response_model=ApiResponse,
    summary="Get the latest state for every truck in the fleet",
    description=(
        "Returns one record per known truck_id, each being the newest stored state. "
        "Resolved with a single JOIN query — no N+1. "
        "Returns an empty list when no trucks have been registered yet."
    ),
)
def get_fleet_latest(db: Session = Depends(get_db)) -> ApiResponse:
    service = TruckService(db)
    trucks = service.get_fleet_latest()
    return ApiResponse(
        success=True,
        message=f"Found {len(trucks)} truck(s)",
        data=[
            TruckStateOut(
                id=t.id,
                truck_id=t.truck_id,
                waste_type=t.waste_type.value,
                latitude=t.latitude,
                longitude=t.longitude,
                position_timestamp=t.position_timestamp,
                version=t.version,
                created_at=t.created_at,
            ).model_dump(mode="json")
            for t in trucks
        ],
    )


@router.get(
    "/ids",
    response_model=ApiResponse,
    summary="List all known truck IDs",
    description="Returns a flat list of every truck_id that has at least one stored state.",
)
def get_truck_ids(db: Session = Depends(get_db)) -> ApiResponse:
    service = TruckService(db)
    trucks = service.get_fleet_latest()
    ids = [t.truck_id for t in trucks]
    return ApiResponse(
        success=True,
        message=f"Found {len(ids)} truck ID(s)",
        data=ids,
    )


@router.get(
    "/{truck_id}/latest",
    response_model=ApiResponse,
    summary="Get the latest known state for one truck",
    description=(
        "Returns the newest stored state for a truck. This is the recommended "
        "endpoint for clients that poll for near-real-time data."
    ),
)
def get_truck_latest(truck_id: str, db: Session = Depends(get_db)) -> ApiResponse:
    service = TruckService(db)
    state = service.get_latest(truck_id)

    if state is None:
        raise HTTPException(
            status_code=404, detail=f"No current state found for truck '{truck_id}'"
        )

    return ApiResponse(
        success=True,
        message=f"Latest state for truck '{truck_id}'",
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


@router.get(
    "/{truck_id}/history",
    response_model=ApiResponse,
    summary="Get version history for one truck",
    description=(
        "Returns the full stored history for a truck, ordered from newest to oldest."
    ),
)
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
