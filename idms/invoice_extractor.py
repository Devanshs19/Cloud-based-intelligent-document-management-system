"""Extract structured fields from invoice text using regular expressions.

Handles common Indian invoice formats (GSTIN, INR / Rs. amounts,
DD/MM/YYYY dates). Missing fields come back as None.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

INVOICE_NO = re.compile(
    r"invoice\s*(?:no\.?|number|#|id)\s*[:\-]?\s*([A-Z0-9][A-Z0-9/\-]{2,})", re.I
)
DATE = re.compile(
    r"(?:invoice\s*date|date\s*of\s*issue|dated?)\s*[:\-]?\s*"
    r"(\d{1,2}[/\-.]\d{1,2}[/\-.]\d{2,4}|\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{4}|\d{4}-\d{2}-\d{2})",
    re.I,
)
# 15 chars: 2-digit state code, 10-char PAN, entity no., 'Z', checksum
GSTIN = re.compile(r"\b(\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z])\b")
EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
AMOUNT = r"(?:₹|rs\.?|inr)?\s*([\d,]+(?:\.\d{1,2})?)"
TOTAL = re.compile(
    r"(?:grand\s*total|total\s*amount|amount\s*due|net\s*payable|total)\s*[:\-]?\s*" + AMOUNT,
    re.I,
)
TAX = re.compile(r"(?:total\s*tax|igst|cgst\s*\+\s*sgst|gst)\s*(?:@\s*\d+%)?\s*[:\-]?\s*" + AMOUNT, re.I)


@dataclass
class InvoiceFields:
    invoice_number: str | None = None
    invoice_date: str | None = None
    gstin: list[str] | None = None
    email: str | None = None
    total_amount: float | None = None
    tax_amount: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @property
    def filled_ratio(self) -> float:
        values = list(asdict(self).values())
        return sum(v is not None for v in values) / len(values)


def _to_float(raw: str) -> float | None:
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


def _largest_amount(pattern: re.Pattern, text: str) -> float | None:
    # "Total" can appear on several lines (subtotal, total...); the grand
    # total is almost always the largest of them.
    values = [v for v in (_to_float(m) for m in pattern.findall(text)) if v is not None]
    return max(values) if values else None


def extract_invoice_fields(text: str) -> InvoiceFields:
    inv = INVOICE_NO.search(text)
    date = DATE.search(text)
    email = EMAIL.search(text)
    gstins = list(dict.fromkeys(GSTIN.findall(text)))  # unique, keep order
    return InvoiceFields(
        invoice_number=inv.group(1) if inv else None,
        invoice_date=date.group(1) if date else None,
        gstin=gstins or None,
        email=email.group(0) if email else None,
        total_amount=_largest_amount(TOTAL, text),
        tax_amount=_largest_amount(TAX, text),
    )
