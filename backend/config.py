"""
config.py – Application settings loaded from .env using python-dotenv.

Usage::

    from config import settings
    print(settings.claude_model)
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Load .env from the project root (one level above this file)
# ---------------------------------------------------------------------------
_ROOT: Path = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT / ".env")


@dataclass
class Settings:
    """Central configuration object.

    All values are read from environment variables (or their defaults) once
    at import time.  Access the pre-built singleton via ``settings``.

    Attributes
    ----------
    anthropic_api_key:
        Secret key for the Anthropic API.  Must be set in ``.env``.
    cap_text_path:
        Absolute path to the extracted CAP plain-text file.
    claude_model:
        Anthropic model identifier used for every stage.
    temp_assessment:
        Sampling temperature for Stage 1 (deterministic fact-finding).
    temp_planning:
        Sampling temperature for Stage 2 (structured planning).
    temp_evaluator:
        Sampling temperature for Stage 3 evaluator agents (diverse viewpoints).
    temp_memo:
        Sampling temperature for Stage 4 memo generation.
    temp_synthesis:
        Sampling temperature for Stage 5 synthesis.
    max_tokens_stage1 … max_tokens_stage5:
        Per-stage token budgets for the LLM response.
    host:
        Uvicorn bind host.
    port:
        Uvicorn bind port.
    """

    # ------------------------------------------------------------------
    # Secrets / paths (from .env)
    # ------------------------------------------------------------------
    anthropic_api_key: str = field(
        default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", "")
    )
    cap_text_path: Path = field(
        default_factory=lambda: _ROOT
        / os.getenv("CAP_TEXT_PATH", "data/2021_Phoenix_CAP.txt")
    )

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------
    claude_model: str = field(
        default_factory=lambda: os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
    )

    # ------------------------------------------------------------------
    # Temperature per stage
    # ------------------------------------------------------------------
    temp_assessment: float = 0.0   # Stage 1 – deterministic assessment
    temp_planning: float = 0.2     # Stage 2 – structured planning
    temp_evaluator: float = 0.5    # Stage 3 – diverse evaluator perspectives
    temp_memo: float = 0.3         # Stage 4 – memo drafting
    temp_synthesis: float = 0.3    # Stage 5 – final synthesis

    # ------------------------------------------------------------------
    # Max tokens per stage
    # ------------------------------------------------------------------
    max_tokens_stage1: int = 3500
    max_tokens_stage2: int = 2500
    max_tokens_stage3: int = 1800
    max_tokens_stage4: int = 1800
    max_tokens_stage5: int = 600

    # ------------------------------------------------------------------
    # Server
    # ------------------------------------------------------------------
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))

    def validate(self) -> None:
        """Raise :class:`ValueError` early if any critical setting is missing.

        Call this once at application startup (e.g. in the FastAPI lifespan
        handler) so the process fails fast rather than at request time.
        """
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY is not set. "
                "Copy .env.example to .env and add your key."
            )
        if not self.cap_text_path:
            raise ValueError(
                "CAP_TEXT_PATH is not configured. "
                "Ensure CAP_TEXT_PATH is set in .env or use the default."
            )


# ---------------------------------------------------------------------------
# Module-level singleton – import this everywhere
# ---------------------------------------------------------------------------
settings: Settings = Settings()
