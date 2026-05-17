"""
stage5_synthesis.py – Stage 5: Synthesis Agent.

Calls the Claude API to consolidate the three evaluator feedback reports
into a unified synthesis: consensus concerns, divergent concerns, priority
revision list, and an overall readiness rating.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage5 import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import EvalWeights, EvaluatorFeedback, SynthesisReport

# ---------------------------------------------------------------------------
# Module-level Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_list_section(text: str, section_label: str) -> list[str]:
    """
    Extract a numbered or bulleted list that follows a bold section header.

    Parameters
    ----------
    text:
        Raw LLM output.
    section_label:
        The section title to search for (case-insensitive, without ``**``).

    Returns
    -------
    list[str]
        Stripped list of item strings found under that section, or an
        empty list if the section is not found.
    """
    pattern = (
        rf"\*\*{re.escape(section_label)}:?\*\*\s*(.*?)"
        r"(?=\*\*[A-Z]|\Z)"
    )
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    block = match.group(1)
    items: list[str] = []
    for line in block.splitlines():
        stripped = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
        if stripped:
            items.append(stripped)
    return items


def _extract_readiness(text: str) -> str:
    """
    Extract the overall readiness rating from the synthesis output.

    Looks for ``READY``, ``NEEDS REVISION``, or ``MAJOR REWORK`` in the
    ``OVERALL READINESS`` section, returning the full sentence/paragraph.

    Parameters
    ----------
    text:
        Raw LLM output from the synthesis agent.

    Returns
    -------
    str
        The readiness rating with its rationale, or an empty string if
        not found.
    """
    match = re.search(
        r"\*\*OVERALL READINESS:?\*\*\s*(.*?)(?=\n\n|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if match:
        return " ".join(match.group(1).split())

    # Fallback: scan for rating keyword anywhere
    keyword_match = re.search(
        r"(READY|NEEDS\s+REVISION|MAJOR\s+REWORK)",
        text,
        re.IGNORECASE,
    )
    return keyword_match.group(1).strip() if keyword_match else "Not determined"


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage5(
    idea: str,
    stage3a: EvaluatorFeedback,
    stage3b: EvaluatorFeedback,
    stage3c: EvaluatorFeedback,
    weights: EvalWeights,
) -> SynthesisReport:
    """Run the Stage 5 Synthesis Agent.

    Consolidates feedback from the Neutral Evaluator, Phoenix Citizen, and
    ADEQ Analyst into a structured synthesis that identifies consensus and
    divergent concerns, lists priority revisions, and rates overall readiness.

    Parameters
    ----------
    idea:
        The policy idea text submitted by the user.
    stage3a:
        Completed :class:`~schemas.EvaluatorFeedback` from the Neutral
        Evaluator (Stage 3a).
    stage3b:
        Completed :class:`~schemas.EvaluatorFeedback` from the Phoenix
        Citizen (Stage 3b).
    stage3c:
        Completed :class:`~schemas.EvaluatorFeedback` from the ADEQ
        Analyst (Stage 3c).
    weights:
        Evaluation criteria weights provided by the user (0–10 scale each).

    Returns
    -------
    SynthesisReport
        Parsed synthesis with concern lists, priority revisions, and
        readiness rating.  On API error the ``raw_output`` field contains
        the error message and all lists contain a single error sentinel string.
    """
    weights_json = json.dumps(weights.model_dump(), indent=2)

    user_message = USER_TEMPLATE.format(
        idea=idea,
        stage3a_output=stage3a.raw_output,
        stage3b_output=stage3b.raw_output,
        stage3c_output=stage3c.raw_output,
        weights_json=weights_json,
    )

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage5,
            temperature=0.3,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_output: str = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Console logging
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        usage = response.usage
        print(
            f"[Stage 5 – Synthesis] {timestamp} | "
            f"input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens}"
        )

        consensus_concerns = _extract_list_section(raw_output, "CONSENSUS CONCERNS")
        divergent_concerns = _extract_list_section(raw_output, "DIVERGENT CONCERNS")
        priority_revisions = _extract_list_section(raw_output, "PRIORITY REVISION LIST")
        overall_readiness = _extract_readiness(raw_output)

        return SynthesisReport(
            consensus_concerns=consensus_concerns,
            divergent_concerns=divergent_concerns,
            priority_revisions=priority_revisions,
            overall_readiness=overall_readiness,
            raw_output=raw_output,
        )

    except Exception as exc:  # noqa: BLE001
        ts = datetime.now(tz=timezone.utc).isoformat()
        error_msg = f"Agent failed: {exc}"
        print(f"[Stage 5 – Synthesis] ERROR at {ts}: {exc}")
        return SynthesisReport(
            consensus_concerns=["Error"],
            divergent_concerns=["Error"],
            priority_revisions=["Error"],
            overall_readiness="Error",
            raw_output=error_msg,
        )
