"""
main.py – FastAPI application entry point.

Run with::

    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import sys
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# Ensure the backend directory is on the path when running from the project root
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse

from config import settings
from cap_text import get_cap_context
from schemas import IdeaInput
from orchestrator import run_pipeline
import exporter

# ---------------------------------------------------------------------------
# Agent imports (validates all modules load correctly at startup)
# ---------------------------------------------------------------------------
from agents.stage1_assessment import run_stage1 as _stage1  # noqa: F401
from agents.stage2_planning import run_stage2 as _stage2  # noqa: F401
from agents.stage3a_neutral import run_stage3a as _stage3a  # noqa: F401
from agents.stage3b_citizen import run_stage3b as _stage3b  # noqa: F401
from agents.stage3c_adeq import run_stage3c as _stage3c  # noqa: F401
from agents.stage4_memo import run_stage4 as _stage4  # noqa: F401
from agents.stage5_synthesis import run_stage5 as _stage5  # noqa: F401


# ---------------------------------------------------------------------------
# Lifespan – runs once on startup and once on shutdown
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context manager.

    On **startup**:

    1. Validates that all required settings (API key, paths) are present.
    2. Loads the Phoenix CAP document and stores it on ``app.state`` so every
       request handler can access it without re-reading the file.

    Raises
    ------
    ValueError
        If settings validation fails (missing API key, etc.).
    FileNotFoundError
        If the CAP text file does not exist on disk.
    """
    # 1. Validate config first so we fail fast on missing secrets
    settings.validate()

    # 2. Load & cache the CAP document
    try:
        cap_context: str = get_cap_context()
        app.state.cap_context = cap_context
        app.state.cap_chars = len(cap_context)
        app.state.cap_loaded = True
        print("CAP loaded successfully")
    except (FileNotFoundError, ValueError) as exc:
        app.state.cap_loaded = False
        app.state.cap_chars = 0
        app.state.cap_context = ""
        raise RuntimeError(f"Failed to load CAP document at startup: {exc}") from exc

    yield  # application runs here

    # Shutdown logic (nothing needed; lru_cache is cleared automatically)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Phoenix CAP Policy Analysis API",
    description=(
        "Multi-agent GenAI pipeline for evaluating policy ideas against the "
        "2021 Phoenix Climate Action Plan."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS – allow the Vite dev server and production frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://phoenix-cap-policy-analysis-1.onrender.com",
        "https://phoenix-cap-frontend.onrender.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["Meta"])
async def health_check() -> dict:
    """Liveness / readiness probe.

    Returns
    -------
    dict
        ``status``
            Always ``"ok"`` if the server is running.
        ``cap_loaded``
            ``True`` when the CAP document was successfully loaded on startup.
        ``cap_chars``
            Number of characters in the loaded CAP context string (including
            the XML wrapper added by :func:`~cap_text.get_cap_context`).
        ``model``
            The Anthropic model configured for this deployment.
    """
    return {
        "status": "ok",
        "cap_loaded": getattr(app.state, "cap_loaded", False),
        "cap_chars": getattr(app.state, "cap_chars", 0),
        "model": settings.claude_model,
    }


@app.post("/api/run", tags=["Pipeline"])
async def run_analysis(payload: IdeaInput) -> dict:
    """Execute the multi-agent policy analysis pipeline.

    Parameters
    ----------
    payload:
        The user's policy idea together with optional pipeline configuration
        flags (e.g. ``mode``, ``weights``).

    Returns
    -------
    dict
        Serialised pipeline result including all stage outputs and timestamps.

    Raises
    ------
    HTTPException
        ``500`` if any stage of the pipeline raises an unexpected error.

    Notes
    -----
    * **MVP mode** (default): Stages 1, 2, and 4.
    * **Full mode**: All 5 stages including multi-perspective evaluators.
    """
    try:
        cap_context: str = getattr(app.state, "cap_context", "")
        result = run_pipeline(payload, cap_context)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline error: {exc}",
        ) from exc

    return result


@app.post("/api/export/docx", tags=["Export"])
async def export_docx(result: dict) -> FileResponse:
    """Export the pipeline result as a formatted Word document (.docx).

    Parameters
    ----------
    result:
        The full pipeline result JSON returned by ``POST /api/run``.

    Returns
    -------
    FileResponse
        A downloadable ``.docx`` file containing the full analysis.

    Raises
    ------
    HTTPException
        ``500`` if document generation fails.
    """
    try:
        file_path = exporter.export_docx(result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"DOCX export error: {exc}",
        ) from exc

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="phoenix_cap_analysis.docx",
    )


@app.post("/api/export/markdown", tags=["Export"])
async def export_markdown(result: dict) -> PlainTextResponse:
    """Export the pipeline result as Markdown plain text.

    Parameters
    ----------
    result:
        The full pipeline result JSON returned by ``POST /api/run``.

    Returns
    -------
    PlainTextResponse
        The full analysis as a Markdown-formatted string.

    Raises
    ------
    HTTPException
        ``500`` if Markdown generation fails.
    """
    try:
        markdown = exporter.export_markdown(result)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Markdown export error: {exc}",
        ) from exc

    return PlainTextResponse(content=markdown, media_type="text/markdown")
