"""
cap_text.py – Loads the extracted Phoenix CAP plain-text file from disk.

The text is read once per process (via :func:`lru_cache`) and exposed through
two public helpers:

* :func:`load_cap_text` – returns the raw, whitespace-normalised string.
* :func:`get_cap_context` – wraps the text in ``<phoenix_cap_document>`` XML
  tags ready to be injected into a prompt.

Typical usage::

    from cap_text import get_cap_context
    context = get_cap_context()   # call on startup; cached after first call
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

from config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MIN_CHARS: int = 100_000          # sanity-check lower bound
_SENTINEL: str = "Climate Action Plan"  # must appear in the document


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def load_cap_text() -> str:
    """Read the full CAP text file, normalise whitespace, and return it.

    The file is read **once** per process lifetime; subsequent calls return
    the cached result instantly.

    Returns
    -------
    str
        The full, whitespace-normalised CAP document as a single string.

    Raises
    ------
    FileNotFoundError
        If :attr:`~config.Settings.cap_text_path` does not exist on disk.
    ValueError
        If the file appears truncated (< 100 000 chars) or does not contain
        the expected sentinel phrase ``"Climate Action Plan"``.
    """
    configured_path: Path = settings.cap_text_path
    fallback_path: Path = Path(__file__).resolve().parent / "data" / "2021_Phoenix_CAP.txt"

    path_candidates = [configured_path]
    if fallback_path not in path_candidates:
        path_candidates.append(fallback_path)

    path = next((candidate for candidate in path_candidates if candidate.exists()), None)
    if path is None:
        tried = ", ".join(f"'{p}'" for p in path_candidates)
        raise FileNotFoundError(
            f"CAP text file not found. Paths checked: {tried}. "
            "Run 'python scripts/extract_cap.py' (or 'bash scripts/setup.sh') first."
        )

    raw: str = path.read_text(encoding="utf-8")

    # ------------------------------------------------------------------
    # Whitespace normalisation
    # Collapse runs of 3+ blank lines down to two (preserves section breaks)
    # while keeping single/double blank lines intact for readability.
    # Also strip leading/trailing whitespace from every line.
    # ------------------------------------------------------------------
    lines = [line.rstrip() for line in raw.splitlines()]
    # Collapse 3+ consecutive blank lines → 2 blank lines
    normalised_lines: list[str] = []
    blank_run: int = 0
    for line in lines:
        if line == "":
            blank_run += 1
            if blank_run <= 2:
                normalised_lines.append(line)
        else:
            blank_run = 0
            normalised_lines.append(line)

    text: str = "\n".join(normalised_lines).strip()

    # ------------------------------------------------------------------
    # Sanity checks
    # ------------------------------------------------------------------
    char_count: int = len(text)

    if _SENTINEL not in text:
        raise ValueError(
            f"CAP text at '{path}' does not contain the expected phrase "
            f'"{_SENTINEL}". The file may be corrupted or incorrect.'
        )

    if char_count < _MIN_CHARS:
        raise ValueError(
            f"CAP text at '{path}' is suspiciously short ({char_count:,} chars; "
            f"expected ≥ {_MIN_CHARS:,}). Re-run the extraction script."
        )

    print(f"Phoenix CAP loaded: {char_count:,} characters")
    return text


def get_cap_context() -> str:
    """Return the full CAP text wrapped in XML tags for prompt injection.

    The XML wrapper helps the model clearly delimit the reference document
    from the rest of the prompt.

    Returns
    -------
    str
        The document enclosed in ``<phoenix_cap_document>`` tags::

            <phoenix_cap_document>
            {full_text}
            </phoenix_cap_document>
    """
    full_text: str = load_cap_text()
    return f"<phoenix_cap_document>\n{full_text}\n</phoenix_cap_document>"


def get_cap_excerpt(max_chars: int = 120_000) -> str:
    """Return up to *max_chars* characters of the raw CAP text.

    Useful when you need to stay within a strict context-window budget but
    still want the beginning of the document.

    Parameters
    ----------
    max_chars:
        Maximum number of characters to return.  Defaults to 120 000.

    Returns
    -------
    str
        The first *max_chars* characters of the normalised CAP text.
    """
    return load_cap_text()[:max_chars]
