"""
stage1_assessment.py – Stage 1: Idea Assessment Agent.

Calls the Claude API to evaluate a policy idea against the Phoenix CAP
across five dimensions: alignment, conflict, equity, feasibility, and
implementation pathway.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage1 import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import AssessmentReport, EvalWeights

# ---------------------------------------------------------------------------
# Module-level Anthropic client (shared within this process)
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)


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


def _extract_finding(text: str, section_header: str) -> str:
    """
    Extract the finding label that follows a section header.

    Supports both legacy ``[Finding: VALUE]`` and current ``**Finding: VALUE**`` formats,
    and both ``**HEADER**`` and ``## HEADER`` section heading styles.
    """
    # Locate section header (## style or **bold** style)
    header_re = re.compile(
        rf"(?:^#{{1,3}}\s+{re.escape(section_header)}|\*\*{re.escape(section_header)}\*\*)[^\n]*$",
        re.IGNORECASE | re.MULTILINE,
    )
    m = header_re.search(text)
    if not m:
        return ""

    after = text[m.end():]
    # Stop at the next section heading
    stopper = re.search(r"(?:^#{1,3}\s+|\*\*\d+\.)", after, re.MULTILINE)
    section_text = after[: stopper.start()] if stopper else after[:800]

    # [Finding: ...] format (legacy)
    bracket = re.search(r"\[Finding:\s*([^\]]+)\]", section_text, re.IGNORECASE)
    if bracket:
        return bracket.group(1).strip()

    # **Finding: ...** format (current model)
    bold = re.search(r"\*\*Finding:\s*([^*\n]+)\*\*", section_text, re.IGNORECASE)
    if bold:
        return bold.group(1).strip()

    return ""


def _extract_citations(text: str) -> list[str]:
    """
    Extract all CAP citations from raw text.

    Matches patterns like ``CAP Goal H2``, ``CAP p. 151``,
    ``CAP Strategy SES1``, ``CAP Section 3``, etc.

    Parameters
    ----------
    text:
        Raw LLM output string.

    Returns
    -------
    list[str]
        Deduplicated list of citation strings, preserving order of first
        occurrence.
    """
    # Require explicit keyword; use p\. (with period) to avoid "CAP provides/practices"
    pattern = (
        r"CAP\s+(?:Goal|Strategy|Section|Action)\s+[A-Z][A-Z0-9\-\.]+"
        r"|CAP\s+p\.\s*\d+"
    )
    matches = re.findall(pattern, text, re.IGNORECASE)
    seen: set[str] = set()
    citations: list[str] = []
    for m in matches:
        normalised = " ".join(m.split())
        if normalised not in seen:
            seen.add(normalised)
            citations.append(normalised)
    return citations


def _extract_overall_verdict(text: str) -> str:
    """
    Extract the text that follows the ``OVERALL VERDICT`` header.

    Parameters
    ----------
    text:
        Raw LLM output.

    Returns
    -------
    str
        The verdict paragraph, or an empty string if the header is not found.
    """
    match = re.search(
        r"(?:#{1,3}\s+OVERALL VERDICT|\*\*OVERALL VERDICT\*\*)\s*(.*?)(?=\n#{1,3}\s+|\Z)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage1(
    idea: str,
    cap_context: str,
    weights: EvalWeights,
) -> AssessmentReport:
    """Run the Stage 1 Idea Assessment Agent.

    Sends the policy idea and relevant CAP context to Claude and parses the
    structured response into an :class:`~schemas.AssessmentReport`.

    Parameters
    ----------
    idea:
        The policy idea text submitted by the user.
    cap_context:
        Relevant excerpt(s) from the Phoenix Climate Action Plan.
    weights:
        Evaluation criteria weights provided by the user (0–10 scale each).

    Returns
    -------
    AssessmentReport
        Parsed assessment with per-dimension findings, verdict, and citations.
        On API error the ``raw_output`` field contains the error message and
        all finding fields are set to ``"Error"``.
    """
    weights_block = _build_weights_block(weights)
    weights_json = json.dumps(weights.model_dump(), indent=2)

    system_prompt = SYSTEM_PROMPT.format(
        weights_block=weights_block,
        idea=idea,
    )
    user_message = USER_TEMPLATE.format(
        idea=idea,
        cap_context=cap_context,
        weights_json=weights_json,
    )

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage1,
            temperature=settings.temp_assessment,
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
            f"[Stage 1 – Assessment] {timestamp} | "
            f"input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens}"
        )

        # Parse structured fields
        alignment_finding = _extract_finding(raw_output, "1. EXISTING ALIGNMENT")
        conflict_finding = _extract_finding(raw_output, "2. CONFLICT CHECK")
        equity_finding = _extract_finding(raw_output, "3. EQUITY ASSESSMENT")
        feasibility_finding = _extract_finding(raw_output, "4. FISCAL FEASIBILITY")
        overall_verdict = _extract_overall_verdict(raw_output)
        citations = _extract_citations(raw_output)

        # Extract implementation pathway section (supports both ## and ** heading styles)
        pathway_match = re.search(
            r"(?:#{1,3}\s+5\. IMPLEMENTATION PATHWAY|\*\*5\. IMPLEMENTATION PATHWAY\*\*)"
            r"\s*(.*?)(?=(?:#{1,3}\s+|\*\*)OVERALL VERDICT|\Z)",
            raw_output,
            re.IGNORECASE | re.DOTALL,
        )
        implementation_pathway = (
            pathway_match.group(1).strip() if pathway_match else ""
        )

        return AssessmentReport(
            idea=idea,
            alignment_finding=alignment_finding or "Not found",
            conflict_finding=conflict_finding or "Not found",
            equity_finding=equity_finding or "Not found",
            feasibility_finding=feasibility_finding or "Not found",
            implementation_pathway=implementation_pathway,
            overall_verdict=overall_verdict or "Not found",
            raw_output=raw_output,
            citations=citations,
        )

    except Exception as exc:  # noqa: BLE001
        print(f"Claude API error in Stage 1: {str(exc)}")
        print(f"Model used: {settings.claude_model}")
        print(f"API key prefix: {settings.anthropic_api_key[:10] if settings.anthropic_api_key else 'NOT SET'}")
        raise
