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

import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.models.schemas import (
    AskRequest,
    AskResponse,
    ChatMessageResponse,
    ConversationResponse,
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
from app.services.database import (
    ConversationNotFoundError,
    create_conversation,
    get_owned_conversation,
    list_conversations,
    list_messages,
    lock_conversation,
    recent_conversation_history,
    save_chat_turn,
)
from app.services.security import get_current_user, require_admin
from app.utils.config import settings  # VECTOR_DB path

router = APIRouter()
templates = Jinja2Templates(directory="templates")
logger = logging.getLogger(__name__)


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Direct visitors to sign in before using the chat interface."""
    return RedirectResponse(url="/login", status_code=303)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {})


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    try:
        get_current_user(request, credentials=None)
    except HTTPException:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "index.html", {})


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
    _admin: dict = Depends(require_admin),
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
def ask(
    payload: AskRequest,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """
    Ask a question. Answer is strictly grounded in retrieved document
    chunks and gated by confidence; low-confidence or ungrounded
    results come back as refusals from the graph itself, not as
    HTTP errors.
    """
    try:
        conversation_id = payload.conversation_id or uuid4()
        if payload.conversation_id:
            if not get_owned_conversation(user["id"], conversation_id):
                raise HTTPException(status_code=404, detail="Conversation not found.")
        else:
            create_conversation(user["id"], "New chat", conversation_id)

        with lock_conversation(conversation_id):
            conversation_key = f"{user['id']}:{conversation_id}"
            history = recent_conversation_history(user["id"], conversation_id)
            result = ask_question(
                payload.question,
                conversation_key,
                request.app.state.compiled_graph,
                conversation_history=history,
                response_conversation_id=str(conversation_id),
            )
            save_chat_turn(
                user_id=user["id"],
                conversation_id=conversation_id,
                question=payload.question,
                answer=result.answer,
                confidence_score=result.confidence_score,
                reason=result.reason,
                sources=[source.model_dump(mode="json") for source in result.sources],
            )
        return result
    except GraphNotReadyError as exc:
        # Distinct from a refusal: this means the agent pipeline itself
        # isn't wired up, which is a server configuration issue (503),
        # not "no answer found" (which the graph would express as a
        # normal low-confidence AskResponse).
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except HTTPException:
        raise
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found.") from exc
    except Exception as exc:
        logger.exception("Failed to process authenticated chat request")
        raise HTTPException(
            status_code=500, detail="Failed to process question. Please try again."
        ) from exc


@router.get("/sources", response_model=SourcesResponse)
async def sources(_user: dict = Depends(get_current_user)):
    """List documents currently present in the FAISS vector store."""
    docs = list_ingested_sources()
    return SourcesResponse(documents=docs)


@router.get("/api/conversations", response_model=list[ConversationResponse])
def conversations(user: dict = Depends(get_current_user)):
    return list_conversations(user["id"])


@router.post(
    "/api/conversations",
    response_model=ConversationResponse,
    status_code=201,
)
def new_conversation(user: dict = Depends(get_current_user)):
    return create_conversation(user["id"])


@router.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[ChatMessageResponse],
)
def conversation_messages(
    conversation_id: UUID,
    user: dict = Depends(get_current_user),
):
    try:
        return list_messages(user["id"], conversation_id)
    except ConversationNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found.") from exc
