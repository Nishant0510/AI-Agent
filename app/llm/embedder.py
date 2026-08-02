from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache

EMBEDDING_MODEL_NAME = "BAAI/bge-base-en-v1.5"


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load once, reuse across the app (loading is slow — don't do it per-request)."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME, device="cpu")


def embed_texts(texts: list[str]) -> np.ndarray:
    """Embed a batch of texts. bge models recommend normalizing embeddings for cosine similarity."""
    model = get_embedder()
    embeddings = model.encode(
        texts,
        normalize_embeddings=True,   # important: enables cosine similarity via inner product in FAISS
        show_progress_bar=True,
        batch_size=32,
    )
    return np.array(embeddings, dtype="float32")


def embed_query(query: str) -> np.ndarray:
    """Embed a single query. bge models recommend a specific instruction prefix for queries."""
    model = get_embedder()
    # bge-base recommends this prefix for retrieval queries (not for the documents being indexed)
    prefixed = f"Represent this sentence for searching relevant passages: {query}"
    embedding = model.encode([prefixed], normalize_embeddings=True)
    return np.array(embedding, dtype="float32")