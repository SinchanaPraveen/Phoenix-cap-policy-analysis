"""
stage3a_neutral.py – Stage 3a: Neutral Policy Evaluator Agent.

Calls the Claude API to evaluate logical consistency, evidence gaps,
and top risks from a neutral, non-ideological perspective.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage3a import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import AssessmentReport, EvalWeights, EvaluatorFeedback, ImplementationRoadmap

# ---------------------------------------------------------------------------
# Module-level Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

AGENT_NAME = "Neutral Evaluator"


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
    Parse the structured risk and revision fields from the neutral evaluator output.

    Extracts ``risk_1``, ``risk_2``, ``risk_3``, and ``revisions`` keys from
    the ``RISK ASSESSMENT`` and ``RECOMMENDED REVISIONS`` sections.

    Parameters
    ----------
    text:
        Raw LLM output from the neutral evaluator.

    Returns
    -------
    dict[str, str]
        Dictionary with keys ``risk_1``, ``risk_2``, ``risk_3``,
        ``revisions``, and ``logical_consistency`` / ``evidence_gaps``
        where present.
    """
    findings: dict[str, str] = {}

    # Extract individual risks: "Risk N: ... — Low/Medium/High"
    risk_matches = re.findall(
        r"Risk\s*(\d):\s*(.*?)(?=Risk\s*\d:|\*\*RECOMMENDED|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    for num, body in risk_matches:
        findings[f"risk_{num}"] = " ".join(body.split())

    # Extract recommended revisions block
    rev_match = re.search(
        r"\*\*RECOMMENDED REVISIONS\*\*\s*(.*?)(?=\n\n|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if rev_match:
        findings["revisions"] = " ".join(rev_match.group(1).split())

    # Extract logical consistency summary
    lc_match = re.search(
        r"\*\*LOGICAL CONSISTENCY\*\*\s*(.*?)(?=\*\*EVIDENCE GAPS\*\*|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if lc_match:
        findings["logical_consistency"] = " ".join(lc_match.group(1).split())

    # Extract evidence gaps
    eg_match = re.search(
        r"\*\*EVIDENCE GAPS\*\*\s*(.*?)(?=\*\*RISK ASSESSMENT\*\*|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if eg_match:
        findings["evidence_gaps"] = " ".join(eg_match.group(1).split())

    return findings


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage3a(
    idea: str,
    cap_context: str,
    stage1: AssessmentReport,
    stage2: ImplementationRoadmap,
    weights: EvalWeights,
) -> EvaluatorFeedback:
    """Run the Stage 3a Neutral Policy Evaluator Agent.

    Evaluates logical consistency, evidence gaps, and the top three risks
    of the proposed idea and roadmap from a neutral analytical stance.

    Parameters
    ----------
    idea:
        The policy idea text submitted by the user.
    cap_context:
        Relevant excerpt(s) from the Phoenix Climate Action Plan.
    stage1:
        Completed :class:`~schemas.AssessmentReport` from Stage 1.
    stage2:
        Completed :class:`~schemas.ImplementationRoadmap` from Stage 2.
    weights:
        Evaluation criteria weights provided by the user (0–10 scale each).

    Returns
    -------
    EvaluatorFeedback
        Parsed findings dict with risk and revision entries.  On API error
        the ``raw_output`` field contains the error message and ``findings``
        holds a single ``"error"`` key.
    """
    weights_block = _build_weights_block(weights)
    weights_json = json.dumps(weights.model_dump(), indent=2)

    system_prompt = SYSTEM_PROMPT.format(weights_block=weights_block)
    user_message = USER_TEMPLATE.format(
        idea=idea,
        stage1_output=stage1.raw_output,
        stage2_output=stage2.raw_output,
        cap_context=cap_context,
        weights_json=weights_json,
    )

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage3,
            temperature=0.5,
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
            f"[Stage 3a – Neutral Evaluator] {timestamp} | "
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
        print(f"[Stage 3a – Neutral Evaluator] ERROR at {ts}: {exc}")
        return EvaluatorFeedback(
            agent_name=AGENT_NAME,
            findings={"error": error_msg},
            raw_output=error_msg,
        )
