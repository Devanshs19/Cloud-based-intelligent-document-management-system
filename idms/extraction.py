"""Text extraction from PDF documents using PyMuPDF.

Pages that contain no extractable text (typically scanned images) are
flagged with ``needs_ocr=True`` so a later OCR stage can handle them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

# A page with fewer characters than this is treated as a scanned image.
MIN_TEXT_CHARS = 20


@dataclass
class PageText:
    page_number: int  # 1-based
    text: str
    needs_ocr: bool


@dataclass
class ExtractedDocument:
    source: str
    page_count: int
    pages: list[PageText] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text)

    @property
    def ocr_pages(self) -> list[int]:
        return [p.page_number for p in self.pages if p.needs_ocr]


def extract_pdf(path: str | Path) -> ExtractedDocument:
    """Extract text from every page of a PDF file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.name}")

    with pymupdf.open(path) as doc:
        pages = []
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text").strip()
            pages.append(
                PageText(page_number=i, text=text, needs_ocr=len(text) < MIN_TEXT_CHARS)
            )
        metadata = {k: v for k, v in (doc.metadata or {}).items() if v}
        return ExtractedDocument(
            source=str(path), page_count=doc.page_count, pages=pages, metadata=metadata
        )
