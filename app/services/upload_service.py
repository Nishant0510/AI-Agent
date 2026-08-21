#app/services/upload_service.py
"""
Handles PDF upload: saves the file to the configured data directory
and triggers (queues) re-ingestion as a background task.

NOTE: This assumes app/ingestion exposes a callable `run_ingestion()`
function that build_vector_database.py can also call from its CLI
entry point, so upload-triggered ingestion and manual ingestion share
one code path. If that function doesn't exist yet, wire it up before
enabling the background trigger below — see the TODO.
"""

import shutil
from pathlib import Path

from fastapi import UploadFile, BackgroundTasks

from app.utils.config import settings  # expects DATA_DIRECTORY, etc.
from build_vector_database import run_ingestion

ALLOWED_CONTENT_TYPE = "application/pdf"


class InvalidFileTypeError(ValueError):
    pass


def _validate_pdf(file: UploadFile) -> None:
    if file.content_type != ALLOWED_CONTENT_TYPE:
        raise InvalidFileTypeError(
            f"Expected a PDF, got content_type={file.content_type!r}"
        )
    if not file.filename.lower().endswith(".pdf"):
        raise InvalidFileTypeError("Uploaded file must have a .pdf extension")


def save_uploaded_pdf(file: UploadFile) -> Path:
    """Validate and persist an uploaded PDF into DATA_DIRECTORY."""
    _validate_pdf(file)

    data_dir = Path(settings.data_directory)
    data_dir.mkdir(parents=True, exist_ok=True)

    destination = data_dir / file.filename
    with destination.open("wb") as out_file:
        shutil.copyfileobj(file.file, out_file)

    return destination


def queue_ingestion(background_tasks: BackgroundTasks) -> None:
    """Queue a full re-ingestion run after upload."""
    background_tasks.add_task(run_ingestion)