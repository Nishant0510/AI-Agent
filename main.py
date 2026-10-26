"""
Application entry point for the Philips Product Knowledge AI Agent.

Wires together:
- FastAPI app instance
- Static file mounting (static/) for CSS/JS
- Jinja2 templates (templates/) for the chat UI
- API router from app.api.routes

Run with: uvicorn main:app --reload
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.postgres import PostgresSaver

from app.agent.graph.build_graph import build_graph
from app.api.routes import router as api_router
from app.api.auth_routes import router as auth_router
from app.services.database import initialize_database, provision_admin
from app.services.security import hash_password
from app.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Keep the PostgreSQL checkpointer open for the app's lifetime."""
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL must be configured to start the application."
        )
    if len(settings.jwt_secret_key) < 32 or settings.jwt_secret_key.startswith("replace-"):
        raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters.")
    if len(settings.admin_password) < 12 or settings.admin_password.startswith("replace-"):
        raise RuntimeError("ADMIN_PASSWORD must contain at least 12 characters.")
    if settings.jwt_expire_minutes <= 0:
        raise RuntimeError("JWT_EXPIRE_MINUTES must be greater than zero.")
    if not settings.admin_email or "@" not in settings.admin_email:
        raise RuntimeError("ADMIN_EMAIL must be a valid account identifier.")

    # Additive tables for account, conversation, and message persistence.
    initialize_database()
    provision_admin(settings.admin_email, hash_password(settings.admin_password))

    with PostgresSaver.from_conn_string(settings.database_url) as checkpointer:
        # Creates or migrates the LangGraph checkpoint tables on first startup.
        checkpointer.setup()
        app.state.compiled_graph = build_graph(checkpointer)
        yield


app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade multi-agent RAG system for grounded "
                 "Philips product documentation Q&A.",
    lifespan=lifespan,
)

# Serves static/css and static/js referenced by templates/index.html
# via url_for('static', path='...')
app.mount("/static", StaticFiles(directory="static"), name="static")

# All routes (/, /health, /upload, /ask, /sources) live in app/api/routes.py
app.include_router(api_router)
app.include_router(auth_router)
