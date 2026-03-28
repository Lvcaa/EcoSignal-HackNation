from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.carbon.climatiq_client import CarbonProviderError
from app.core.database import get_db
from app.schemas.carbon import (
    CarbonBatchEvaluationRequest,
    CarbonEvaluationRequest,
    PersonalDailyFootprintRequest,
)
from app.schemas.common import ApiResponse
from app.services.carbon_service import CarbonService

router = APIRouter(prefix="/api/v1/carbon", tags=["carbon"])


def _raise_provider_error(exc: CarbonProviderError) -> None:
    raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post(
    "/evaluate",
    response_model=ApiResponse,
    summary="Evaluate a deterministic carbon footprint activity",
    description=(
        "Evaluates one explicit activity using a pinned deterministic Climatiq selector."
    ),
)
def evaluate_carbon(payload: CarbonEvaluationRequest) -> ApiResponse:
    service = CarbonService()
    try:
        result = service.evaluate(payload)
    except CarbonProviderError as exc:
        _raise_provider_error(exc)
    return ApiResponse(
        success=True,
        message=f"Carbon evaluation completed for '{payload.activity_type.value}'",
        data=result.model_dump(mode="json"),
    )


@router.post(
    "/evaluate/batch",
    response_model=ApiResponse,
    summary="Evaluate a batch of deterministic carbon activities",
    description="Evaluates multiple explicit activities and returns itemized results plus a total.",
)
def evaluate_carbon_batch(payload: CarbonBatchEvaluationRequest) -> ApiResponse:
    service = CarbonService()
    try:
        result = service.evaluate_batch(payload)
    except CarbonProviderError as exc:
        _raise_provider_error(exc)
    return ApiResponse(
        success=True,
        message=f"Carbon batch evaluation completed for {result.accepted} item(s)",
        data=result.model_dump(mode="json"),
    )


@router.post(
    "/personal/evaluate",
    response_model=ApiResponse,
    summary="Evaluate one person's daily carbon footprint",
    description=(
        "Accepts structured daily habits and returns a deterministic, itemized carbon footprint."
    ),
)
def evaluate_personal_daily(payload: PersonalDailyFootprintRequest) -> ApiResponse:
    service = CarbonService()
    try:
        result = service.evaluate_personal_daily(payload)
    except CarbonProviderError as exc:
        _raise_provider_error(exc)
    return ApiResponse(
        success=True,
        message=f"Daily personal carbon footprint evaluated for '{payload.person_id}'",
        data=result.model_dump(mode="json"),
    )


@router.get(
    "/personal/habits",
    response_model=ApiResponse,
    summary="List deterministic personal habit templates",
    description=(
        "Returns the supported personal habit templates and their fixed deterministic expansions."
    ),
)
def get_personal_habits() -> ApiResponse:
    service = CarbonService()
    result = service.get_personal_habit_catalog()
    return ApiResponse(
        success=True,
        message=f"Loaded {len(result.habits)} personal habit template(s)",
        data=result.model_dump(mode="json"),
    )


@router.get(
    "/factors",
    response_model=ApiResponse,
    summary="List pinned carbon factors and selectors",
    description="Returns the deterministic activity catalog, pinned selectors, and metadata used by the carbon module.",
)
def get_carbon_factors() -> ApiResponse:
    service = CarbonService()
    result = service.get_factor_catalog()
    return ApiResponse(
        success=True,
        message=f"Loaded {len(result.factors)} carbon factor mapping(s)",
        data=result.model_dump(mode="json"),
    )


@router.get(
    "/trucks/{truck_id}/latest",
    response_model=ApiResponse,
    summary="Derive the latest cumulative carbon footprint for one truck",
    description=(
        "Reads the existing truck history and derives a cumulative carbon footprint without altering truck state."
    ),
)
def get_truck_carbon_latest(
    truck_id: str, db: Session = Depends(get_db)
) -> ApiResponse:
    service = CarbonService(db)
    try:
        result = service.derive_latest_truck_footprint(truck_id)
    except CarbonProviderError as exc:
        _raise_provider_error(exc)

    if result is None:
        raise HTTPException(
            status_code=404, detail=f"No current state found for truck '{truck_id}'"
        )

    return ApiResponse(
        success=True,
        message=f"Derived carbon footprint for truck '{truck_id}'",
        data=result.model_dump(mode="json"),
    )


@router.get(
    "/trucks/{truck_id}/history",
    response_model=ApiResponse,
    summary="Derive carbon footprint history for one truck",
    description=(
        "Returns segment-by-segment derived carbon evaluations using the existing immutable truck history."
    ),
)
def get_truck_carbon_history(
    truck_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = CarbonService(db)
    try:
        result = service.derive_truck_history(truck_id, page=page, page_size=page_size)
    except CarbonProviderError as exc:
        _raise_provider_error(exc)

    if result is None:
        raise HTTPException(
            status_code=404, detail=f"No history found for truck '{truck_id}'"
        )

    return ApiResponse(
        success=True,
        message=f"Derived {result.total} carbon segment(s) for truck '{truck_id}'",
        data=result.model_dump(mode="json"),
    )
