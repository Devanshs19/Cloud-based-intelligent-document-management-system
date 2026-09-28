"""Rule-based document classifier.

A simple keyword-scoring baseline. It needs no training data, so it works
from day one and gives the team a baseline to compare an ML classifier
against later (e.g. on the RVL-CDIP dataset).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Keyword -> weight for each document type. Weights > 1 mark strong signals.
KEYWORDS: dict[str, dict[str, float]] = {
    "invoice": {
        "invoice": 3, "tax invoice": 3, "bill to": 2, "gstin": 2, "invoice no": 3,
        "amount due": 2, "subtotal": 1, "total": 1, "qty": 1, "hsn": 2, "due date": 1,
    },
    "receipt": {
        "receipt": 3, "payment received": 2, "paid": 1, "cash": 1,
        "change": 1, "thank you for your purchase": 2, "transaction id": 2,
    },
    "resume": {
        "resume": 3, "curriculum vitae": 3, "experience": 1, "education": 1,
        "skills": 1, "projects": 1, "objective": 1, "linkedin": 2, "cgpa": 2,
    },
    "contract": {
        "agreement": 3, "hereinafter": 3, "party": 1, "parties": 1, "terms and conditions": 2,
        "witness": 1, "termination": 2, "governing law": 2, "whereas": 2,
    },
    "report": {
        "abstract": 2, "introduction": 1, "conclusion": 1, "references": 1,
        "methodology": 2, "results": 1, "table of contents": 2, "summary": 1,
    },
}


@dataclass
class Classification:
    label: str
    confidence: float  # 0..1, share of the total score the winner got
    scores: dict[str, float]


def _count(term: str, text: str) -> int:
    return len(re.findall(r"\b" + re.escape(term) + r"\b", text))


def classify(text: str, min_score: float = 3.0) -> Classification:
    """Classify a document by keyword scores. Returns 'other' if no strong match."""
    lowered = text.lower()
    scores = {
        label: sum(weight * min(_count(term, lowered), 3) for term, weight in terms.items())
        for label, terms in KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    total = sum(scores.values())
    if scores[best] < min_score or total == 0:
        return Classification("other", 0.0, scores)
    return Classification(best, round(scores[best] / total, 3), scores)
