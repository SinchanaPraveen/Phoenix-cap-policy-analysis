"""
One-time setup script: extract text from the Phoenix CAP PDF.

Usage:
    python scripts/extract_cap.py

Output:
    data/2021_Phoenix_CAP.txt
"""

import os
import sys

# ---------------------------------------------------------------------------
# Paths (relative to the project root, i.e. the directory this script is
# called from)
# ---------------------------------------------------------------------------
PDF_PATH = os.path.join("data", "2021_Phoenix_CAP_compressed.pdf")
TXT_PATH = os.path.join("data", "2021_Phoenix_CAP.txt")
MIN_CHARS = 100_000  # validation threshold


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Gracefully handle a missing PDF
    # ------------------------------------------------------------------
    if not os.path.exists(PDF_PATH):
        print(
            f"ERROR: PDF file not found at '{PDF_PATH}'.\n"
            "Please make sure 'data/2021_Phoenix_CAP_compressed.pdf' exists "
            "in the project root before running this script."
        )
        sys.exit(1)

    try:
        import pdfplumber  # noqa: PLC0415 – intentional late import
    except ImportError:
        print(
            "ERROR: pdfplumber is not installed.\n"
            "Run:  pip install -r backend/requirements.txt"
        )
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Extract text page by page
    # ------------------------------------------------------------------
    pages_text: list[str] = []
    skipped: list[int] = []

    with pdfplumber.open(PDF_PATH) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            page_num = i + 1  # 1-based for human-readable output

            # Progress report every 20 pages
            if page_num % 20 == 0:
                print(f"Extracting page {page_num} of {total_pages}...")

            raw_text = page.extract_text()

            # Handle pages with no extractable text
            if not raw_text or not raw_text.strip():
                print(f"Page {page_num}: no text found, skipping")
                skipped.append(page_num)
                continue

            # Strip excessive whitespace while preserving section structure:
            #   • collapse runs of 3+ blank lines down to 2
            #   • strip trailing spaces from every line
            lines = raw_text.splitlines()
            cleaned_lines: list[str] = []
            blank_run = 0
            for line in lines:
                stripped = line.rstrip()
                if stripped == "":
                    blank_run += 1
                    if blank_run <= 2:          # allow at most 2 consecutive blank lines
                        cleaned_lines.append("")
                else:
                    blank_run = 0
                    cleaned_lines.append(stripped)

            cleaned_text = "\n".join(cleaned_lines).strip()

            pages_text.append((page_num, cleaned_text))

    # ------------------------------------------------------------------
    # 3. Join all pages with the numbered separator
    # ------------------------------------------------------------------
    segments: list[str] = []
    for page_num, text in pages_text:
        segments.append(f"\n--- PAGE {page_num} ---\n")
        segments.append(text)

    full_text = "\n".join(segments)

    # ------------------------------------------------------------------
    # 4. Save to disk
    # ------------------------------------------------------------------
    os.makedirs(os.path.dirname(TXT_PATH), exist_ok=True)
    with open(TXT_PATH, "w", encoding="utf-8") as fh:
        fh.write(full_text)

    char_count = len(full_text)
    print(
        f"Done. Extracted {total_pages} pages, "
        f"{char_count:,} characters saved to {TXT_PATH}"
    )
    if skipped:
        print(f"  (Skipped {len(skipped)} page(s) with no extractable text: {skipped})")

    # ------------------------------------------------------------------
    # 5. Quick validation
    # ------------------------------------------------------------------
    if not os.path.exists(TXT_PATH):
        print(f"VALIDATION FAILED: output file '{TXT_PATH}' does not exist.")
        sys.exit(1)

    actual_size = os.path.getsize(TXT_PATH)  # bytes ≈ chars for UTF-8 ASCII text
    actual_chars = len(open(TXT_PATH, encoding="utf-8").read())

    if actual_chars < MIN_CHARS:
        print(
            f"VALIDATION WARNING: output file contains only {actual_chars:,} characters "
            f"(expected > {MIN_CHARS:,}). The extraction may be incomplete."
        )
        sys.exit(1)
    else:
        print(
            f"Validation passed: {TXT_PATH} exists and contains "
            f"{actual_chars:,} characters (> {MIN_CHARS:,} threshold)."
        )


if __name__ == "__main__":
    main()
