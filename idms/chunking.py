"""Split document text into overlapping chunks for embeddings / vector storage.

Chunks are built from whole sentences where possible, so a chunk never
cuts a sentence in half unless that sentence alone is longer than the limit.
Sizes are in words (a rough stand-in for tokens: ~0.75 words per token).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n{2,}")


@dataclass
class Chunk:
    chunk_id: int
    text: str
    word_count: int
    source: str | None = None


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s and s.strip()]


def chunk_text(
    text: str, max_words: int = 200, overlap_words: int = 40, source: str | None = None
) -> list[Chunk]:
    if max_words <= 0:
        raise ValueError("max_words must be positive")
    if not 0 <= overlap_words < max_words:
        raise ValueError("overlap_words must be >= 0 and smaller than max_words")

    # Break over-long sentences into max_words pieces first.
    units: list[list[str]] = []
    for sentence in _split_sentences(text):
        words = sentence.split()
        for i in range(0, len(words), max_words):
            units.append(words[i : i + max_words])

    chunks: list[Chunk] = []
    current: list[str] = []
    for unit in units:
        if current and len(current) + len(unit) > max_words:
            chunks.append(Chunk(len(chunks), " ".join(current), len(current), source))
            current = current[-overlap_words:] if overlap_words else []
            # Drop overlap if it would still overflow with the next unit.
            if len(current) + len(unit) > max_words:
                current = []
        current.extend(unit)
    if current:
        chunks.append(Chunk(len(chunks), " ".join(current), len(current), source))
    return chunks
