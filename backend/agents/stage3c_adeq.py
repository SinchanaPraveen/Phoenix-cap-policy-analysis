"""
stage3c_adeq.py – Stage 3c: ADEQ Analyst Evaluator Agent.

Calls the Claude API to evaluate the policy idea from the perspective of
an Arizona Department of Environmental Quality (ADEQ) regulatory analyst,
covering regulatory alignment, jurisdictional analysis, technical review,
and statewide implications.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage3c import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import AssessmentReport, EvalWeights, EvaluatorFeedback, ImplementationRoadmap

# ---------------------------------------------------------------------------
# Module-level Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

AGENT_NAME = "ADEQ Analyst"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_weights_block(weights: EvalWeights) -> str:
    """Format EvalWeights as a human-readable block for the system prompt."""
    return (
        f"Effectiveness: {weights.effectiveness:.0f}/10, "
        f"Efficiency: {weights.efficiency:.0f}/10, "
        f"Equity: {weights.equity:.0f}/10, "
        f"Liberty: {weights.liberty:.0f}/10, "
        f"Political Feasibility: {weights.political_feasibility:.0f}/10, "
        f"Social Acceptability: {weights.social_acceptability:.0f}/10, "
        f"Administrative Feasibility: {weights.administrative_feasibility:.0f}/10"
    )


def _parse_findings(text: str) -> dict[str, str]:
    """
    Parse the ADEQ technical review sections into a structured findings dict.

    Extracts ``regulatory_alignment``, ``jurisdictional_analysis``,
    ``technical_review``, ``statewide_implications``, and
    ``adeq_recommendation`` from the formatted output.

    Parameters
    ----------
    text:
        Raw LLM output from the ADEQ analyst evaluator.

    Returns
    -------
    dict[str, str]
        Dictionary with keys for each ADEQ review section.
    """
    findings: dict[str, str] = {}

    sections = {
        "regulatory_alignment": (
            r"\*\*REGULATORY ALIGNMENT\*\*\s*(.*?)(?=\*\*JURISDICTIONAL ANALYSIS|\Z)"
        ),
        "jurisdictional_analysis": (
            r"\*\*JURISDICTIONAL ANALYSIS\*\*\s*(.*?)(?=\*\*TECHNICAL REVIEW|\Z)"
        ),
        "technical_review": (
            r"\*\*TECHNICAL REVIEW\*\*\s*(.*?)(?=\*\*STATEWIDE IMPLICATIONS|\Z)"
        ),
        "statewide_implications": (
            r"\*\*STATEWIDE IMPLICATIONS\*\*\s*(.*?)(?=\*\*ADEQ RECOMMENDATION|\Z)"
        ),
        "adeq_recommendation": (
            r"\*\*ADEQ RECOMMENDATION\*\*\s*(.*?)(?=\n\n|\Z)"
        ),
    }

    for key, pattern in sections.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            findings[key] = " ".join(match.group(1).split())

    return findings


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage3c(
    idea: str,
    stage1: AssessmentReport,
    stage2: ImplementationRoadmap,
    weights: EvalWeights,
) -> EvaluatorFeedback:
    """Run the Stage 3c ADEQ Analyst Evaluator Agent.

    Evaluates the policy idea and roadmap through an ADEQ regulatory lens,
    covering compliance with state environmental law, jurisdictional
    boundaries, technical measurability, and statewide precedent.

    Parameters
    ----------
    idea:
        The policy idea text submitted by the user.
    stage1:
        Completed :class:`~schemas.AssessmentReport` from Stage 1.
    stage2:
        Completed :class:`~schemas.ImplementationRoadmap` from Stage 2.
    weights:
        Evaluation criteria weights provided by the user (0–10 scale each).

    Returns
    -------
    EvaluatorFeedback
        Parsed findings dict with ADEQ review sections and recommendation.
        On API error the ``raw_output`` field contains the error message and
        ``findings`` holds a single ``"error"`` key.
    """
    weights_block = _build_weights_block(weights)
    weights_json = json.dumps(weights.model_dump(), indent=2)

    system_prompt = SYSTEM_PROMPT.format(weights_block=weights_block)
    user_message = USER_TEMPLATE.format(
        idea=idea,
        stage1_output=stage1.raw_output,
        stage2_output=stage2.raw_output,
        weights_json=weights_json,
    )

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage3,
            temperature=0.3,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_output: str = "".join(
            block.text for block in response.content if block.type == "text"
        )

        # Console logging
        timestamp = datetime.now(tz=timezone.utc).isoformat()
        usage = response.usage
        print(
            f"[Stage 3c – ADEQ Analyst] {timestamp} | "
            f"input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens}"
        )

        findings = _parse_findings(raw_output)

        return EvaluatorFeedback(
            agent_name=AGENT_NAME,
            findings=findings,
            raw_output=raw_output,
        )

    except Exception as exc:  # noqa: BLE001
        ts = datetime.now(tz=timezone.utc).isoformat()
        error_msg = f"Agent failed: {exc}"
        print(f"[Stage 3c – ADEQ Analyst] ERROR at {ts}: {exc}")
        return EvaluatorFeedback(
            agent_name=AGENT_NAME,
            findings={"error": error_msg},
            raw_output=error_msg,
        )
