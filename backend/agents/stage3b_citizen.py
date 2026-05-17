"""
stage3b_citizen.py – Stage 3b: Phoenix Citizen Evaluator Agent.

Calls the Claude API to simulate the perspective of a Phoenix resident
in a heat-vulnerable, low-income neighborhood, focusing on lived
experience, equity, and community buy-in.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage3b import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import AssessmentReport, EvalWeights, EvaluatorFeedback, ImplementationRoadmap

# ---------------------------------------------------------------------------
# Module-level Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

AGENT_NAME = "Phoenix Citizen"


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
    Parse the citizen feedback sections into a structured findings dict.

    Extracts ``neighborhood_impact``, ``equity_analysis``, ``concerns``,
    and ``buy_in_conditions`` from the formatted output.

    Parameters
    ----------
    text:
        Raw LLM output from the citizen evaluator.

    Returns
    -------
    dict[str, str]
        Dictionary with keys for each feedback section.
    """
    findings: dict[str, str] = {}

    sections = {
        "neighborhood_impact": r"\*\*WHAT THIS MEANS FOR MY NEIGHBORHOOD\*\*\s*(.*?)(?=\*\*WHO BENEFITS|\Z)",
        "equity_analysis": r"\*\*WHO BENEFITS / WHO MIGHT BE LEFT OUT\*\*\s*(.*?)(?=\*\*MY MAIN CONCERNS|\Z)",
        "concerns": r"\*\*MY MAIN CONCERNS\*\*\s*(.*?)(?=\*\*WHAT WOULD MAKE|\Z)",
        "buy_in_conditions": r"\*\*WHAT WOULD MAKE ME SUPPORT THIS\*\*\s*(.*?)(?=\n\n|\Z)",
    }

    for key, pattern in sections.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            findings[key] = " ".join(match.group(1).split())

    return findings


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage3b(
    idea: str,
    stage1: AssessmentReport,
    stage2: ImplementationRoadmap,
    weights: EvalWeights,
) -> EvaluatorFeedback:
    """Run the Stage 3b Phoenix Citizen Evaluator Agent.

    Simulates feedback from a Phoenix resident in a heat-vulnerable,
    low-income neighborhood, covering neighborhood impact, equity analysis,
    top concerns, and conditions for community support.

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
        Parsed findings dict with citizen perspective sections.  On API
        error the ``raw_output`` field contains the error message and
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
            temperature=0.6,
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
            f"[Stage 3b – Phoenix Citizen] {timestamp} | "
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
        print(f"[Stage 3b – Phoenix Citizen] ERROR at {ts}: {exc}")
        return EvaluatorFeedback(
            agent_name=AGENT_NAME,
            findings={"error": error_msg},
            raw_output=error_msg,
        )
