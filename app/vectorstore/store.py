#app/vectorstore/store.py
from pathlib import Path
from datetime import datetime
from pathlib import Path
from app.vectorstore.faiss_store import load_index
from app.models.schemas import SourceDocument
from app.utils.config import settings
from collections import Counter
from app.vectorstore.faiss_store import (
    INDEX_FILENAME,
    METADATA_FILENAME,
)

def vector_store_exists() -> bool:
    db_path = Path(settings.vector_db)

    return (
        (db_path / INDEX_FILENAME).exists()
        and
        (db_path / METADATA_FILENAME).exists()
    )

def list_documents() -> list[SourceDocument]:
    """
    Return one SourceDocument per unique PDF currently stored in the
    vector database.

    The chunk metadata is loaded from chunks.pkl and grouped by
    document_name.
    """
    if not vector_store_exists():
        return []

    _, chunks = load_index(settings.vector_db)

    counts = Counter(
        chunk.metadata.document_name
        for chunk in chunks
    )

    # Use the metadata file's modification time as the ingestion timestamp.
    metadata_path = Path(settings.vector_db) / METADATA_FILENAME
    last_ingested = datetime.fromtimestamp(
        metadata_path.stat().st_mtime
    ).isoformat()

    documents = [
        SourceDocument(
            document=document_name,
            num_chunks=num_chunks,
            last_ingested_at=last_ingested,
        )
        for document_name, num_chunks in sorted(counts.items())
    ]

    return documents    