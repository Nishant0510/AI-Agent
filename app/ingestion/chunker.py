from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.ingestion.pdf_parser import PageText
from app.models.chunk import DocumentChunk, ChunkMetadata

CHUNK_SIZE = 500       # characters; tune based on your embedding model's context
CHUNK_OVERLAP = 50


def chunk_document(document_name: str, pages: list[PageText]) -> list[DocumentChunk]:
    """Split page text into chunks, preserving page number and assigning stable chunk IDs."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    chunks: list[DocumentChunk] = []
    global_index = 0

    for page in pages:
        page_chunks = splitter.split_text(page.text)

        for text in page_chunks:
            chunk_id = f"{_slugify(document_name)}_p{page.page_number}_c{global_index:04d}"
            chunks.append(
                DocumentChunk(
                    text=text,
                    metadata=ChunkMetadata(
                        document_name=document_name,
                        page_number=page.page_number,
                        chunk_id=chunk_id,
                        chunk_index=global_index,
                    ),
                )
            )
            global_index += 1

    return chunks


def _slugify(name: str) -> str:
    return name.replace(" ", "_").replace(".pdf", "")