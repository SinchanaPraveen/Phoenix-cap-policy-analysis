"""
orchestrator.py – Coordinates the multi-agent pipeline.

MVP  mode: Stage 1 → Stage 2 → Stage 4
Full mode: Stage 1 → Stage 2 → Stage 3a / 3b / 3c (sequential) → Stage 5 → Stage 4
"""
from __future__ import annotations
import time
import logging
from datetime import datetime, timezone
from typing import Any

from schemas import IdeaInput


from agents.stage1_assessment import run_stage1
from agents.stage2_planning import run_stage2
from agents.stage3a_neutral import run_stage3a
from agents.stage3b_citizen import run_stage3b
from agents.stage3c_adeq import run_stage3c
from agents.stage4_memo import run_stage4
from agents.stage5_synthesis import run_stage5

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    """Return current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


def _elapsed(start: str) -> float:
    """Return seconds elapsed since *start* (an ISO-8601 UTC timestamp)."""
    t0 = datetime.fromisoformat(start)
    return (datetime.now(tz=timezone.utc) - t0).total_seconds()


def _stage_log(name: str, start: str) -> None:
    """Print a completion banner for *name* with elapsed seconds."""
    print(f"  ✓ {name} completed in {_elapsed(start):.1f}s")


def _stage_error_log(name: str, exc: Exception) -> None:
    """Log a stage failure with name and UTC timestamp."""
    ts = _now()
    logger.error("[%s] FAILED at %s — %s: %s", name, ts, type(exc).__name__, exc)
    print(f"  ✗ {name} FAILED at {ts} — {type(exc).__name__}: {exc}")


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def run_pipeline(input: IdeaInput, cap_context: str) -> dict[str, Any]:
    """
    Execute the full agent pipeline synchronously.

    Parameters
    ----------
    input:
        The validated :class:`~schemas.IdeaInput` from the API request.
    cap_context:
        Pre-loaded Phoenix CAP document text (stored on ``app.state``).

    Returns
    -------
    dict
        Serialisable pipeline result including all stage outputs and a
        ``timestamps`` sub-dict with per-stage start/end times.  If a stage
        fails it is included as ``None`` and a top-level ``stage_errors``
        dict records the failure message for each failed stage.  The pipeline
        never crashes — partial results are always returned.
    """
    idea = input.idea
    weights = input.weights
    mode = input.mode
    timestamps: dict[str, Any] = {}
    stage_errors: dict[str, str] = {}
    cap_context = cap_context[:2000]
    print(f"\n{'='*60}")
    print(f"[Pipeline] Starting — mode={mode!r}  idea={idea[:80]!r}")
    print(f"{'='*60}")

    # ------------------------------------------------------------------
    # Stage 1 – Idea Assessment
    # ------------------------------------------------------------------
    print("[Stage 1] Assessment … starting")
    t1_start = _now()
    timestamps["stage1_start"] = t1_start

    try:
        stage1 = run_stage1(idea, cap_context, weights)
        timestamps["stage1_end"] = _now()
        _stage_log("Stage 1 – Assessment", t1_start)
        print("[Pipeline] Waiting 10s before Stage 2...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 1 – Assessment", exc)
        stage_errors["stage1"] = f"Stage 1 failed: {exc}"
        timestamps["stage1_end"] = _now()
        stage1 = None

    # ------------------------------------------------------------------
    # Stage 2 – Implementation Planning
    # ------------------------------------------------------------------
    print("[Stage 2] Planning … starting")
    t2_start = _now()
    timestamps["stage2_start"] = t2_start

    try:
        if stage1 is None:
            raise RuntimeError("Stage 1 did not complete — skipping Stage 2")
        stage2 = run_stage2(idea, cap_context, stage1, weights)
        timestamps["stage2_end"] = _now()
        _stage_log("Stage 2 – Planning", t2_start)
        print("[Pipeline] Waiting 10s before next stage...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 2 – Planning", exc)
        stage_errors["stage2"] = f"Stage 2 failed: {exc}"
        timestamps["stage2_end"] = _now()
        stage2 = None

    # ------------------------------------------------------------------
    # MVP mode: skip Stage 3 / 5 and go straight to memo
    # ------------------------------------------------------------------
    if mode == "mvp":
        print("[Stage 4] Policy Memo (MVP) … starting")
        t4_start = _now()
        timestamps["stage4_start"] = t4_start

        try:
            if stage1 is None or stage2 is None:
                raise RuntimeError("Earlier stages did not complete — cannot generate memo")
            memo = run_stage4(idea, stage1, stage2, weights)
            timestamps["stage4_end"] = _now()
            _stage_log("Stage 4 – Policy Memo", t4_start)
            print("[Pipeline] Waiting 10s before Stage 3b...")
            time.sleep(10)

        except Exception as exc:  # noqa: BLE001
            _stage_error_log("Stage 4 – Policy Memo", exc)
            stage_errors["stage4"] = f"Stage 4 failed: {exc}"
            timestamps["stage4_end"] = _now()
            memo = None

        timestamps["pipeline_end"] = _now()
        print(
            f"[Pipeline] MVP complete in "
            f"{_elapsed(timestamps['stage1_start']):.1f}s total\n"
        )

        _memo_dict = memo.model_dump() if memo else None
        result: dict[str, Any] = {
            "mode": "mvp",
            "stage1": stage1.model_dump() if stage1 else None,
            "stage2": stage2.model_dump() if stage2 else None,
            "stage4": _memo_dict,
            "memo":   _memo_dict,
            "timestamps": timestamps,
        }
        if stage_errors:
            result["stage_errors"] = stage_errors
        return result

    # ------------------------------------------------------------------
    # Full mode – Stage 3a / 3b / 3c
    # ------------------------------------------------------------------
    print("[Stage 3a] Neutral Evaluator … starting")
    t3a_start = _now()
    timestamps["stage3a_start"] = t3a_start

    try:
        if stage1 is None or stage2 is None:
            raise RuntimeError("Earlier stages did not complete — skipping Stage 3a")
        stage3a = run_stage3a(idea, cap_context, stage1, stage2, weights)
        timestamps["stage3a_end"] = _now()
        _stage_log("Stage 3a – Neutral Evaluator", t3a_start)
        print("[Pipeline] Waiting 10s before Stage 3b...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 3a – Neutral Evaluator", exc)
        stage_errors["stage3a"] = f"Stage 3a failed: {exc}"
        timestamps["stage3a_end"] = _now()
        stage3a = None

    print("[Stage 3b] Citizen Evaluator … starting")
    t3b_start = _now()
    timestamps["stage3b_start"] = t3b_start

    try:
        if stage1 is None or stage2 is None:
            raise RuntimeError("Earlier stages did not complete — skipping Stage 3b")
        stage3b = run_stage3b(idea, stage1, stage2, weights)
        timestamps["stage3b_end"] = _now()
        _stage_log("Stage 3b – Citizen Evaluator", t3b_start)
        print("[Pipeline] Waiting 10s before Stage 3c...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 3b – Citizen Evaluator", exc)
        stage_errors["stage3b"] = f"Stage 3b failed: {exc}"
        timestamps["stage3b_end"] = _now()
        stage3b = None

    print("[Stage 3c] ADEQ Evaluator … starting")
    t3c_start = _now()
    timestamps["stage3c_start"] = t3c_start

    try:
        if stage1 is None or stage2 is None:
            raise RuntimeError("Earlier stages did not complete — skipping Stage 3c")
        stage3c = run_stage3c(idea, stage1, stage2, weights)
        timestamps["stage3c_end"] = _now()
        _stage_log("Stage 3c – ADEQ Evaluator", t3c_start)
        print("[Pipeline] Waiting 10s before Stage 5...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 3c – ADEQ Evaluator", exc)
        stage_errors["stage3c"] = f"Stage 3c failed: {exc}"
        timestamps["stage3c_end"] = _now()
        stage3c = None

    # ------------------------------------------------------------------
    # Stage 5 – Synthesis (full mode only)
    # ------------------------------------------------------------------
    print("[Stage 5] Synthesis … starting")
    t5_start = _now()
    timestamps["stage5_start"] = t5_start

    try:
        if stage3a is None and stage3b is None and stage3c is None:
            raise RuntimeError("All Stage 3 agents failed — cannot synthesise")
        synthesis = run_stage5(idea, stage3a, stage3b, stage3c, weights)
        timestamps["stage5_end"] = _now()
        _stage_log("Stage 5 – Synthesis", t5_start)
        print("[Pipeline] Waiting 10s before Stage 4...")
        time.sleep(10)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 5 – Synthesis", exc)
        stage_errors["stage5"] = f"Stage 5 failed: {exc}"
        timestamps["stage5_end"] = _now()
        synthesis = None

    # ------------------------------------------------------------------
    # Stage 4 – Policy Memo (full mode, with evaluators + synthesis)
    # ------------------------------------------------------------------
    print("[Stage 4] Policy Memo (Full) … starting")
    t4_start = _now()
    timestamps["stage4_start"] = t4_start

    try:
        if stage1 is None or stage2 is None:
            raise RuntimeError("Core stages (1/2) did not complete — cannot generate memo")
        memo = run_stage4(
            idea,
            stage1,
            stage2,
            weights,
            stage3a=stage3a,
            stage3b=stage3b,
            stage3c=stage3c,
            stage5=synthesis,
        )
        timestamps["stage4_end"] = _now()
        _stage_log("Stage 4 – Policy Memo", t4_start)
    except Exception as exc:  # noqa: BLE001
        _stage_error_log("Stage 4 – Policy Memo", exc)
        stage_errors["stage4"] = f"Stage 4 failed: {exc}"
        timestamps["stage4_end"] = _now()
        memo = None

    timestamps["pipeline_end"] = _now()
    print(
        f"[Pipeline] Full pipeline complete in "
        f"{_elapsed(timestamps['stage1_start']):.1f}s total\n"
    )

    _memo_dict = memo.model_dump() if memo else None
    _synthesis_dict = synthesis.model_dump() if synthesis else None
    result = {
        "mode": "full",
        "stage1":    stage1.model_dump()  if stage1   else None,
        "stage2":    stage2.model_dump()  if stage2   else None,
        "stage3a":   stage3a.model_dump() if stage3a  else None,
        "stage3b":   stage3b.model_dump() if stage3b  else None,
        "stage3c":   stage3c.model_dump() if stage3c  else None,
        "stage5":    _synthesis_dict,
        "synthesis": _synthesis_dict,
        "stage4":    _memo_dict,
        "memo":      _memo_dict,
        "timestamps": timestamps,
    }
    if stage_errors:
        result["stage_errors"] = stage_errors
    return result
