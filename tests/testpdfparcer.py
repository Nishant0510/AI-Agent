from pathlib import Path
from app.ingestion.pdf_parser import parse_pdf

pages = parse_pdf(Path("data/users/SimplyGo-Usermanual.pdf"))
print(f"Extracted {len(pages)} non-empty pages")
print(pages[0].page_number, pages[0].text[:200])