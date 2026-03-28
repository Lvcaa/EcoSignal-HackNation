import logging
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.signal import Signal, SignalAttachment
from app.models.signal import SignalType as ModelSignalType
from app.repositories.signal_repository import SignalRepository
from app.schemas.signal import SignalCreateRequest

logger = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB per file
MAX_FILES_PER_UPLOAD = 10


class SignalService:
    def __init__(self, db: Session) -> None:
        self.repo = SignalRepository(db)

    def create_signal(self, payload: SignalCreateRequest) -> Signal:
        signal = Signal(
            title=payload.title,
            description=payload.description,
            signal_type=ModelSignalType(payload.signal_type.value),
            latitude=payload.latitude,
            longitude=payload.longitude,
        )
        created = self.repo.create(signal)
        logger.info("Signal %d created: %s", created.id, created.title)
        return created

    def get_signal(self, signal_id: int) -> Signal | None:
        return self.repo.get_by_id(signal_id)

    def list_signals(
        self, page: int = 1, page_size: int = 50
    ) -> tuple[list[Signal], int]:
        total = self.repo.count()
        if total == 0:
            return [], 0
        skip = (page - 1) * page_size
        signals = self.repo.get_all(skip=skip, limit=page_size)
        return signals, total

    def delete_signal(self, signal_id: int) -> bool:
        signal = self.repo.get_by_id(signal_id)
        if signal is None:
            return False
        for att in signal.attachments:
            file_path = Path(settings.UPLOAD_DIR) / att.storage_path
            if file_path.exists():
                file_path.unlink()
                logger.info("Deleted file: %s", file_path)
        self.repo.delete(signal)
        logger.info("Signal %d deleted", signal_id)
        return True

    async def add_attachments(
        self, signal_id: int, files: list[UploadFile]
    ) -> list[SignalAttachment]:
        signal = self.repo.get_by_id(signal_id)
        if signal is None:
            raise ValueError(f"Signal {signal_id} not found")

        if len(files) > MAX_FILES_PER_UPLOAD:
            raise ValueError(
                f"Too many files: maximum {MAX_FILES_PER_UPLOAD} per request"
            )

        attachments: list[SignalAttachment] = []
        saved_paths: list[Path] = []

        try:
            for file in files:
                if file.content_type not in ALLOWED_CONTENT_TYPES:
                    raise ValueError(
                        f"File '{file.filename}': content type '{file.content_type}' "
                        f"not allowed. Accepted: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}"
                    )

                content = await file.read()
                if len(content) > MAX_FILE_SIZE:
                    raise ValueError(
                        f"File '{file.filename}' exceeds maximum size of "
                        f"{MAX_FILE_SIZE // (1024 * 1024)} MB"
                    )

                ext = Path(file.filename).suffix.lower() if file.filename else ".bin"
                unique_name = f"{uuid.uuid4().hex}{ext}"
                relative_dir = f"signals/{signal_id}"
                relative_path = f"{relative_dir}/{unique_name}"

                abs_dir = Path(settings.UPLOAD_DIR) / relative_dir
                abs_dir.mkdir(parents=True, exist_ok=True)
                abs_path = abs_dir / unique_name
                abs_path.write_bytes(content)
                saved_paths.append(abs_path)

                attachments.append(
                    SignalAttachment(
                        signal_id=signal_id,
                        filename=unique_name,
                        original_filename=file.filename or "unnamed",
                        content_type=file.content_type or "application/octet-stream",
                        file_size=len(content),
                        storage_path=relative_path,
                    )
                )

            created = self.repo.create_attachments_bulk(attachments)
            logger.info(
                "Signal %d: %d attachment(s) uploaded", signal_id, len(created)
            )
            return created

        except Exception:
            for path in saved_paths:
                if path.exists():
                    path.unlink()
            raise

    def get_attachment_path(
        self, signal_id: int, attachment_id: int
    ) -> tuple[Path, str, str] | None:
        att = self.repo.get_attachment_by_id(signal_id, attachment_id)
        if att is None:
            return None
        abs_path = Path(settings.UPLOAD_DIR) / att.storage_path
        if not abs_path.exists():
            logger.warning(
                "Attachment %d file missing from disk: %s", attachment_id, abs_path
            )
            return None
        return abs_path, att.content_type, att.original_filename
