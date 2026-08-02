"""
Application entry point for the Philips Product Knowledge AI Agent.

Wires together:
- FastAPI app instance
- Static file mounting (static/) for CSS/JS
- Jinja2 templates (templates/) for the chat UI
- API router from app.api.routes

Run with: uvicorn main:app --reload
"""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.utils.config import settings

app = FastAPI(
    title=settings.app_name,
    description="Enterprise-grade multi-agent RAG system for grounded "
                 "Philips product documentation Q&A.",
)

# Serves static/css and static/js referenced by templates/index.html
# via url_for('static', path='...')
app.mount("/static", StaticFiles(directory="static"), name="static")

# All routes (/, /health, /upload, /ask, /sources) live in app/api/routes.py
app.include_router(api_router)