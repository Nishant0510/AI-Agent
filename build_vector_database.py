"""
Ingestion entry point. Run this any time PDFs are added to or updated in data/users/.
Usage: python build_vector_database.py
"""
from pathlib import Path
import logging

from app.ingestion.pdf_parser import parse_pdf
from app.ingestion.chunker import chunk_document
from app.llm.embedder import embed_texts
from app.vectorstore.faiss_store import build_index, persist_index
from app.models.chunk import DocumentChunk

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DATA_DIRECTORY = Path("data/users")
VECTOR_DB_PATH = Path("data/vector_db")


def run_ingestion():
    pdf_paths = sorted(DATA_DIRECTORY.glob("*.pdf"))

    if not pdf_paths:
        logger.error(f"No PDFs found in {DATA_DIRECTORY}. Add manuals and re-run.")
        return

    logger.info(f"Found {len(pdf_paths)} PDF(s) to ingest")

    all_chunks: list[DocumentChunk] = []

    for pdf_path in pdf_paths:
        logger.info(f"Parsing {pdf_path.name}")
        pages = parse_pdf(pdf_path)
        logger.info(f"  -> {len(pages)} pages with extractable text")

        if not pages:
            logger.warning(f"  -> No text extracted from {pdf_path.name} (possibly scanned/image-only PDF). Skipping.")
            continue

        chunks = chunk_document(pdf_path.name, pages)
        logger.info(f"  -> {len(chunks)} chunks created")
        all_chunks.extend(chunks)

    if not all_chunks:
        logger.error("No chunks were produced from any document. Aborting index build.")
        return

    logger.info(f"Embedding {len(all_chunks)} chunks total (this may take a while on CPU)...")
    texts = [chunk.text for chunk in all_chunks]
    embeddings = embed_texts(texts)

    logger.info("Building FAISS index...")
    index = build_index(all_chunks, embeddings)

    logger.info(f"Persisting index to {VECTOR_DB_PATH}...")
    persist_index(index, all_chunks, VECTOR_DB_PATH)

    logger.info(f"✅ Done. Indexed {len(all_chunks)} chunks from {len(pdf_paths)} document(s).")


def main():
    run_ingestion()

if __name__ == "__main__":
    main()