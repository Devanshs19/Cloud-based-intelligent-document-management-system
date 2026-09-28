import sys
from pathlib import Path

import pymupdf
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SAMPLE_INVOICE = """TAX INVOICE
ABC Traders Pvt Ltd
GSTIN: 29ABCDE1234F1Z5
Email: billing@abctraders.in
Invoice No: INV-2024/0042
Invoice Date: 15/03/2024
Bill To: XYZ Solutions
Item            Qty   Rate     Amount
Laptop Stand     2    1500.00  3000.00
USB-C Hub        1    2000.00  2000.00
Subtotal: 5000.00
GST @18%: 900.00
Grand Total: Rs. 5,900.00
"""


def make_pdf(path: Path, pages: list[str]) -> Path:
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        if text:
            page.insert_text((50, 60), text, fontsize=10)
    doc.save(path)
    doc.close()
    return path


@pytest.fixture
def invoice_pdf(tmp_path):
    return make_pdf(tmp_path / "invoice.pdf", [SAMPLE_INVOICE])


@pytest.fixture
def blank_page_pdf(tmp_path):
    return make_pdf(tmp_path / "scan.pdf", [SAMPLE_INVOICE, ""])
