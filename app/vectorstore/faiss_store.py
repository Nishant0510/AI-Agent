#app/vectorstore/faiss_store.py
import faiss
import numpy as np
import pickle
from pathlib import Path
from app.models.chunk import DocumentChunk
from app.models.retrieval import RetrievedChunk
from pathlib import Path

INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "chunks.pkl"


def build_index(chunks: list[DocumentChunk], embeddings: np.ndarray) -> faiss.Index:
    """Build a FAISS index using inner product (cosine similarity, since embeddings are normalized)."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # IP = inner product; works as cosine sim on normalized vectors
    index.add(embeddings)
    return index


def persist_index(index: faiss.Index, chunks: list[DocumentChunk], vector_db_path: Path) -> None:
    """Save the FAISS index and a parallel list of chunk metadata (position i in list = vector i in index)."""
    vector_db_path.mkdir(parents=True, exist_ok=True)

    faiss.write_index(index, str(vector_db_path / INDEX_FILENAME))

    with open(vector_db_path / METADATA_FILENAME, "wb") as f:
        pickle.dump(chunks, f)




def load_index(vector_db_path: Path | str) -> tuple[faiss.Index, list[DocumentChunk]]:
    vector_db_path = Path(vector_db_path)

    index = faiss.read_index(str(vector_db_path / INDEX_FILENAME))

    with open(vector_db_path / METADATA_FILENAME, "rb") as f:
        chunks = pickle.load(f)

    return index, chunks


# def search(index: faiss.Index, chunks: list[DocumentChunk], query_embedding: np.ndarray, top_k: int = 5):
#     """Search the index and return chunks with similarity scores, mapping FAISS int IDs back to metadata."""
#     scores, indices = index.search(query_embedding, top_k)

#     results = []
#     for score, idx in zip(scores[0], indices[0]):
#         if idx == -1:  # FAISS returns -1 if fewer than top_k results exist
#             continue
#         results.append((chunks[idx], float(score)))

#     return results

def search(
    index: faiss.Index,
    chunks: list[DocumentChunk],
    query_embedding: np.ndarray,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """
    Search the FAISS index and return the top-k retrieved chunks with
    similarity scores.
    """
    scores, indices = index.search(query_embedding, top_k)

    results: list[RetrievedChunk] = []

    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue

        chunk = chunks[idx]

        results.append(
            RetrievedChunk(
                document=chunk.metadata.document_name,
                page=chunk.metadata.page_number,
                chunk_id=chunk.metadata.chunk_id,
                text=chunk.text,
                similarity_score=float(score),
            )
        )

    return results