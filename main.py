"""Command-line entry point.

Usage:
    python main.py path/to/file.pdf               # summary to terminal
    python main.py path/to/file.pdf -o out.json   # full result as JSON
    python main.py path/to/folder/                # every PDF in a folder
"""

import argparse
import json
import sys
from pathlib import Path

from idms.pipeline import process_document


def summarize(result: dict) -> str:
    c = result["classification"]
    lines = [
        f"File       : {result['file']}",
        f"Pages      : {result['page_count']}  (need OCR: {result['pages_needing_ocr'] or 'none'})",
        f"Type       : {c['label']}  (confidence {c['confidence']:.0%})",
        f"Chunks     : {result['chunk_count']}",
        f"Time       : {result['processing_time_sec']} s",
    ]
    if result["invoice_fields"]:
        lines.append("Invoice fields:")
        lines += [f"  {k:<15}: {v}" for k, v in result["invoice_fields"].items()]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Process PDF documents.")
    parser.add_argument("path", help="A PDF file or a folder of PDFs")
    parser.add_argument("-o", "--output", help="Write full JSON results to this file")
    parser.add_argument("--max-words", type=int, default=200)
    parser.add_argument("--overlap", type=int, default=40)
    args = parser.parse_args()

    target = Path(args.path)
    files = sorted(target.glob("*.pdf")) if target.is_dir() else [target]
    if not files:
        print(f"No PDF files found in {target}", file=sys.stderr)
        return 1

    results = []
    for f in files:
        try:
            result = process_document(f, args.max_words, args.overlap)
        except Exception as e:  # keep going on bad files in a batch
            print(f"[error] {f.name}: {e}", file=sys.stderr)
            continue
        results.append(result)
        print(summarize(result), end="\n\n")

    if args.output:
        payload = results[0] if len(results) == 1 else results
        Path(args.output).write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"Saved results to {args.output}")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
