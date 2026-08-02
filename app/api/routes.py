#app/api/routes.py
"""
FastAPI route definitions for the Philips Product Knowledge AI Agent.

Endpoints:
  GET  /        - Web interface (serves the Bootstrap chat UI)
  GET  /health  - Health check
  POST /upload  - Upload a PDF manual, queues re-ingestion
  POST /ask     - Ask a grounded question against the ingested manuals
  GET  /sources - List currently ingested documents
"""

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import (
    AskRequest,
    AskResponse,
    HealthResponse,
    SourcesResponse,
    UploadResponse,
)
from app.services.qa_service import ask_question, GraphNotReadyError
from app.services.upload_service import (
    save_uploaded_pdf,
    queue_ingestion,
    InvalidFileTypeError,
)
from app.services.source_service import list_ingested_sources
from app.utils.config import settings  # VECTOR_DB path

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the Bootstrap chat interface."""
    return templates.TemplateResponse(
    request,
    "index.html",
    {}
)


@router.get("/health", response_model=HealthResponse)
async def health():
    """Basic health check, including whether the vector DB exists on disk."""
    vector_db_path = Path(settings.vector_db)
    return HealthResponse(
        status="ok",
        vector_db_ready=vector_db_path.exists(),
    )


@router.post("/upload", response_model=UploadResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Accept a PDF, save it to data/users/, and queue re-ingestion
    as a background task.
    """
    try:
        saved_path = save_uploaded_pdf(file)
    except InvalidFileTypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to save file: {exc}"
        ) from exc

    queue_ingestion(background_tasks)

    return UploadResponse(
        filename=saved_path.name,
        status="queued_for_ingestion",
        message=(
            "File saved. Re-ingestion has been queued; the document "
            "will be searchable once ingestion completes."
        ),
    )


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest):
    """
    Ask a question. Answer is strictly grounded in retrieved document
    chunks and gated by confidence; low-confidence or ungrounded
    results come back as refusals from the graph itself, not as
    HTTP errors.
    """
    try:
        return ask_question(payload.question)
    except GraphNotReadyError as exc:
        # Distinct from a refusal: this means the agent pipeline itself
        # isn't wired up, which is a server configuration issue (503),
        # not "no answer found" (which the graph would express as a
        # normal low-confidence AskResponse).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to process question: {exc}"
        ) from exc


@router.get("/sources", response_model=SourcesResponse)
async def sources():
    """List documents currently present in the FAISS vector store."""
    docs = list_ingested_sources()
    return SourcesResponse(documents=docs)