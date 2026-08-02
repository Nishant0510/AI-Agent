from pathlib import Path
from pypdf import PdfReader
from pydantic import BaseModel


class PageText(BaseModel):
    page_number: int  # 1-indexed, matches what a human sees in the PDF
    text: str


def parse_pdf(pdf_path: Path) -> list[PageText]:
    """Extract text from a PDF, page by page, keeping page numbers attached."""
    reader = PdfReader(str(pdf_path))
    pages = []

    for i, page in enumerate(reader.pages):
        raw_text = page.extract_text() or ""
        cleaned = _clean_text(raw_text)

        if cleaned.strip():  # skip blank pages (covers, dividers, etc.)
            pages.append(PageText(page_number=i + 1, text=cleaned))

    return pages


def _clean_text(text: str) -> str:
    """Basic cleanup: collapse excess whitespace, fix common PDF extraction artifacts."""
    import re
    text = re.sub(r"\s+", " ", text)          # collapse multiple spaces/newlines
    text = re.sub(r"-\n", "", text)            # rejoin hyphenated line breaks (pre-clean, before collapse ideally)
    return text.strip()