"""Intelligent Document Management System (IDMS) - core processing package.

Pipeline stages implemented here:
    extraction        -> pull text out of PDFs page by page
    classifier        -> guess the document type (invoice, resume, ...)
    invoice_extractor -> pull structured fields out of invoices
    chunking          -> split text into overlapping chunks for embeddings
    pipeline          -> run all of the above on one file
"""

__version__ = "0.1.0"
