"""End-to-end processing of a single document."""

from __future__ import annotations

import time
from dataclasses import asdict
from pathlib import Path

from .chunking import chunk_text
from .classifier import classify
from .extraction import extract_pdf
from .invoice_extractor import extract_invoice_fields


def process_document(path: str | Path, max_words: int = 200, overlap_words: int = 40) -> dict:
    """Extract -> classify -> (invoice fields) -> chunk. Returns a JSON-ready dict."""
    start = time.perf_counter()
    doc = extract_pdf(path)
    text = doc.full_text

    classification = classify(text)
    fields = extract_invoice_fields(text).to_dict() if classification.label == "invoice" else None
    chunks = chunk_text(text, max_words, overlap_words, source=Path(path).name)

    return {
        "file": Path(path).name,
        "page_count": doc.page_count,
        "pages_needing_ocr": doc.ocr_pages,
        "metadata": doc.metadata,
        "classification": asdict(classification),
        "invoice_fields": fields,
        "chunk_count": len(chunks),
        "chunks": [asdict(c) for c in chunks],
        "processing_time_sec": round(time.perf_counter() - start, 4),
    }
