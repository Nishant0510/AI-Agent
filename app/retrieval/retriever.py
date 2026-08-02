# app/retrieval/retriever.py
"""
Loads an existing FAISS index and performs Top-K similarity search
for an incoming query. Assumes the index was already built by the
Phase 1 ingestion pipeline (build_vector_database.py) and persisted
at settings.vector_db.
"""
import logging
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from app.models.retrieval import RetrievalResult, RetrievedChunk
from app.utils.config import settings

logger = logging.getLogger(__name__)

_embedding_model: HuggingFaceEmbeddings | None = None
_vector_store: FAISS | None = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model: %s", settings.embedding_model)
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
            model_kwargs={"device": settings.device},
        )
    return _embedding_model


def load_vector_store() -> FAISS:
    """
    Loads the persisted FAISS index from settings.vector_db.
    Raises FileNotFoundError with a clear message if the index doesn't
    exist yet — callers (e.g. the Document Agent later) should catch
    this and route to a "no documents" response rather than crashing.
    """
    global _vector_store
    if _vector_store is not None:
        return _vector_store

    index_path = Path(settings.vector_db)
    if not index_path.exists():
        raise FileNotFoundError(
            f"No FAISS index found at '{index_path}'. "
            "Run `python build_vector_database.py` first."
        )

    logger.info("Loading FAISS index from %s", index_path)
    _vector_store = FAISS.load_local(
        str(index_path),
        get_embedding_model(),
        allow_dangerous_deserialization=True,
    )
    return _vector_store


def retrieve(query: str, top_k: int | None = None) -> RetrievalResult:
    """
    Embeds the query and performs Top-K similarity search against the
    FAISS index. Returns raw candidate chunks with similarity scores —
    thresholding/gating is NOT done here, that's the Confidence Agent's
    job. This function only retrieves and shapes the data.
    """
    k = top_k or settings.top_k
    store = load_vector_store()

    logger.info("Retrieving top_k=%d chunks for query: %r", k, query)
    results_with_scores = store.similarity_search_with_relevance_scores(query, k=k)

    chunks = []
    for doc, score in results_with_scores:
        metadata = doc.metadata
        chunks.append(
            RetrievedChunk(
                document=metadata.get("source", "unknown"),
                page=metadata.get("page", -1),
                chunk_id=metadata.get("chunk_id", "unknown"),
                text=doc.page_content,
                similarity_score=round(float(score), 4),
            )
        )

    return RetrievalResult(query=query, chunks=chunks)