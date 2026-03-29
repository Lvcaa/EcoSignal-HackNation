from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.report import ReportOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get(
    "/random",
    response_model=ApiResponse,
    summary="Get a random report",
    description=(
        "Returns a single randomly-generated report with a real full-bin photo. "
        "Results are cached for 5 seconds to reduce external API pressure."
    ),
)
def random_report(db: Session = Depends(get_db)) -> ApiResponse:
    service = ReportService(db)
    report = service.generate_random()
    data = ReportOut.model_validate(report).model_dump(mode="json")
    return ApiResponse(
        success=True,
        message="Random report generated",
        data=data,
    )
