import pytest

from conftest import SAMPLE_INVOICE
from idms.chunking import chunk_text
from idms.classifier import classify
from idms.extraction import extract_pdf
from idms.invoice_extractor import extract_invoice_fields
from idms.pipeline import process_document


# ---------- extraction ----------
def test_extract_pdf_reads_text(invoice_pdf):
    doc = extract_pdf(invoice_pdf)
    assert doc.page_count == 1
    assert "Grand Total" in doc.full_text
    assert doc.ocr_pages == []


def test_blank_page_is_flagged_for_ocr(blank_page_pdf):
    assert extract_pdf(blank_page_pdf).ocr_pages == [2]


def test_extract_rejects_missing_and_non_pdf(tmp_path):
    with pytest.raises(FileNotFoundError):
        extract_pdf(tmp_path / "nope.pdf")
    txt = tmp_path / "a.txt"
    txt.write_text("hi")
    with pytest.raises(ValueError):
        extract_pdf(txt)


# ---------- classification ----------
def test_classify_invoice():
    result = classify(SAMPLE_INVOICE)
    assert result.label == "invoice"
    assert 0 < result.confidence <= 1


def test_classify_resume():
    text = "Curriculum Vitae. Education: B.Tech CSE, CGPA 8.9. Skills: Python. Projects: IDMS. LinkedIn profile."
    assert classify(text).label == "resume"


def test_classify_unknown_text_is_other():
    assert classify("The quick brown fox jumps over the lazy dog.").label == "other"


# ---------- invoice fields ----------
def test_invoice_fields():
    f = extract_invoice_fields(SAMPLE_INVOICE)
    assert f.invoice_number == "INV-2024/0042"
    assert f.invoice_date == "15/03/2024"
    assert f.gstin == ["29ABCDE1234F1Z5"]
    assert f.email == "billing@abctraders.in"
    assert f.total_amount == 5900.00
    assert f.tax_amount == 900.00
    assert f.filled_ratio == 1.0


def test_invoice_fields_missing():
    f = extract_invoice_fields("nothing useful here")
    assert f.invoice_number is None and f.total_amount is None
    assert f.filled_ratio == 0.0


# ---------- chunking ----------
def test_chunks_respect_max_words_and_overlap():
    text = " ".join(f"Sentence number {i} has some words." for i in range(100))
    chunks = chunk_text(text, max_words=50, overlap_words=10)
    assert len(chunks) > 1
    assert all(c.word_count <= 50 for c in chunks)
    # each chunk starts with the last 10 words of the previous one
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.text.split()[:10] == prev.text.split()[-10:]


def test_long_sentence_is_split():
    chunks = chunk_text("word " * 500, max_words=100, overlap_words=0)
    assert [c.word_count for c in chunks] == [100] * 5


def test_chunk_invalid_args():
    with pytest.raises(ValueError):
        chunk_text("x", max_words=10, overlap_words=10)


def test_empty_text_gives_no_chunks():
    assert chunk_text("") == []


# ---------- end to end ----------
def test_process_document(invoice_pdf):
    result = process_document(invoice_pdf)
    assert result["classification"]["label"] == "invoice"
    assert result["invoice_fields"]["total_amount"] == 5900.00
    assert result["chunk_count"] >= 1
