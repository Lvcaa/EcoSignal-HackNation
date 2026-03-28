from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.common import ApiResponse
from app.schemas.signal import (
    AttachmentOut,
    SignalCreateRequest,
    SignalListOut,
    SignalOut,
)
from app.services.signal_service import SignalService

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


def _signal_to_out(signal) -> dict:
    return SignalOut(
        id=signal.id,
        title=signal.title,
        description=signal.description,
        signal_type=signal.signal_type.value,
        latitude=signal.latitude,
        longitude=signal.longitude,
        created_at=signal.created_at,
        attachments=[
            AttachmentOut(
                id=a.id,
                signal_id=a.signal_id,
                original_filename=a.original_filename,
                content_type=a.content_type,
                file_size=a.file_size,
                created_at=a.created_at,
            )
            for a in signal.attachments
        ],
    ).model_dump(mode="json")


@router.post(
    "",
    response_model=ApiResponse,
    status_code=201,
    summary="Create a new signal",
    description="Creates a new signal with position, type, title, and description.",
)
def create_signal(
    payload: SignalCreateRequest, db: Session = Depends(get_db)
) -> ApiResponse:
    service = SignalService(db)
    signal = service.create_signal(payload)
    return ApiResponse(
        success=True,
        message=f"Signal {signal.id} created",
        data=_signal_to_out(signal),
    )


@router.get(
    "",
    response_model=ApiResponse,
    summary="List all signals",
    description="Returns all signals ordered by newest first, with pagination.",
)
def list_signals(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = SignalService(db)
    signals, total = service.list_signals(page=page, page_size=page_size)
    return ApiResponse(
        success=True,
        message=f"Found {total} signal(s)",
        data=SignalListOut(
            total=total,
            page=page,
            page_size=page_size,
            signals=[_signal_to_out(s) for s in signals],
        ).model_dump(mode="json"),
    )


@router.get(
    "/{signal_id}",
    response_model=ApiResponse,
    summary="Get a single signal",
    description="Returns a signal with its attachment metadata.",
)
def get_signal(signal_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    service = SignalService(db)
    signal = service.get_signal(signal_id)
    if signal is None:
        raise HTTPException(
            status_code=404, detail=f"Signal {signal_id} not found"
        )
    return ApiResponse(
        success=True,
        message=f"Signal {signal_id}",
        data=_signal_to_out(signal),
    )


@router.post(
    "/{signal_id}/attachments",
    response_model=ApiResponse,
    status_code=201,
    summary="Upload image attachments to a signal",
    description=(
        "Upload one or more images (JPEG, PNG, WebP, GIF). "
        "Maximum 10 files per request, 10 MB per file."
    ),
)
async def upload_attachments(
    signal_id: int,
    files: list[UploadFile] = File(..., description="Image files to upload"),
    db: Session = Depends(get_db),
) -> ApiResponse:
    service = SignalService(db)
    try:
        attachments = await service.add_attachments(signal_id, files)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    return ApiResponse(
        success=True,
        message=f"{len(attachments)} attachment(s) uploaded to signal {signal_id}",
        data=[
            AttachmentOut(
                id=a.id,
                signal_id=a.signal_id,
                original_filename=a.original_filename,
                content_type=a.content_type,
                file_size=a.file_size,
                created_at=a.created_at,
            ).model_dump(mode="json")
            for a in attachments
        ],
    )


@router.get(
    "/{signal_id}/attachments/{attachment_id}",
    summary="Download an attachment image",
    description="Returns the image file as a binary download.",
)
def download_attachment(
    signal_id: int, attachment_id: int, db: Session = Depends(get_db)
):
    service = SignalService(db)
    result = service.get_attachment_path(signal_id, attachment_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Attachment {attachment_id} not found for signal {signal_id}",
        )
    abs_path, content_type, original_filename = result
    return FileResponse(
        path=str(abs_path),
        media_type=content_type,
        filename=original_filename,
    )


@router.delete(
    "/{signal_id}",
    response_model=ApiResponse,
    summary="Delete a signal",
    description="Deletes a signal and all its attachments (files and DB records).",
)
def delete_signal(signal_id: int, db: Session = Depends(get_db)) -> ApiResponse:
    service = SignalService(db)
    deleted = service.delete_signal(signal_id)
    if not deleted:
        raise HTTPException(
            status_code=404, detail=f"Signal {signal_id} not found"
        )
    return ApiResponse(
        success=True,
        message=f"Signal {signal_id} deleted",
    )
