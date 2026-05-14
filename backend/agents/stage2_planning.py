"""
stage2_planning.py – Stage 2: Implementation Planning Agent.

Calls the Claude API to produce a phased implementation roadmap
(quick wins, medium-term, long-term) grounded in the Phoenix CAP,
informed by the Stage 1 assessment.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

import anthropic

from config import settings
from prompts.stage2 import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import AssessmentReport, EvalWeights, ImplementationRoadmap

# ---------------------------------------------------------------------------
# Module-level Anthropic client
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


def _extract_section_items(text: str, section_label: str) -> list[str]:
    """
    Extract action items from a named section in the LLM output.

    Finds the section header regardless of prefix style (##, **, numbered,
    or plain text), captures content until the next major section, then
    returns top-level action titles — filtering out sub-property lines
    (Lead Department, Key Partners, etc.).

    Parameters
    ----------
    text:
        Raw LLM output.
    section_label:
        The section title to search for (case-insensitive).

    Returns
    -------
    list[str]
        Stripped list of action item strings found under that section.
    """
    # Step 1: Find the section header line — flexible prefix matching
    header_re = re.compile(
        rf"^[^\n]*\b{re.escape(section_label)}\b[^\n]*$",
        re.IGNORECASE | re.MULTILINE,
    )
    m = header_re.search(text)
    if not m:
        return []

    # Step 2: Grab content after the header, stop at the next known section
    after = text[m.end():]
    stopper = re.compile(
        r"^\s*(?:#+\s+|\*{1,3}\s*|\d+\.\s+)?"
        r"(?:QUICK WINS|MEDIUM[- ]TERM|LONG[- ]TERM INTEGRATION|EQUITY)\b",
        re.IGNORECASE | re.MULTILINE,
    )
    sm = stopper.search(after)
    block = after[: sm.start()] if sm else after

    # Step 3a: Prefer bold action titles (**Action N: description**)
    _SKIP_LABELS = {
        "lead department", "key partner", "estimated resource",
        "cap anchor", "authority scope", "success metric",
        "key barrier", "equity safeguard",
    }
    bold_items = re.findall(r"\*\*([^*\n]{10,200})\*\*", block)
    if bold_items:
        filtered = [
            b.strip().rstrip(":").strip()
            for b in bold_items
            if not any(sk in b.lower() for sk in _SKIP_LABELS) and len(b.strip()) > 5
        ]
        if filtered:
            return filtered

    # Step 3b: Fallback — plain bullet/numbered items, skip sub-property lines
    _SKIP_RE = re.compile(
        r"^(Lead\b|Key\s+Partner|Estimated\b|CAP\s+Anchor|Authority\s+Scope|"
        r"Success\s+Metric|Key\s+Barrier|Equity\s+Safeguard)",
        re.IGNORECASE,
    )
    items: list[str] = []
    for line in block.splitlines():
        cleaned = re.sub(r"^[\s\*\-•\d\.\)]+", "", line).strip().rstrip("*").strip()
        if cleaned and not _SKIP_RE.match(cleaned):
            items.append(cleaned)
    return items


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage2(
    idea: str,
    cap_context: str,
    stage1: AssessmentReport,
    weights: EvalWeights,
) -> ImplementationRoadmap:
    """Run the Stage 2 Implementation Planning Agent.

    Given the original policy idea, the CAP context, and the Stage 1
    assessment, asks Claude to generate a structured implementation roadmap
    with quick wins, medium-term actions, long-term integration steps, and
    an equity checklist.

    Parameters
    ----------
    idea:
        The policy idea text submitted by the user.
    cap_context:
        Relevant excerpt(s) from the Phoenix Climate Action Plan.
    stage1:
        Completed :class:`~schemas.AssessmentReport` from Stage 1.
    weights:
        Evaluation criteria weights provided by the user (0–10 scale each).

    Returns
    -------
    ImplementationRoadmap
        Parsed roadmap with tiered action lists.  On API error the
        ``raw_output`` field contains the error message and all lists are
        populated with a single error sentinel string.
    """
    weights_block = _build_weights_block(weights)
    weights_json = json.dumps(weights.model_dump(), indent=2)

    system_prompt = SYSTEM_PROMPT.format(weights_block=weights_block)
    user_message = USER_TEMPLATE.format(
        idea=idea,
        stage1_output=stage1.raw_output,
        cap_context=cap_context,
        weights_json=weights_json,
    )

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage2,
            temperature=settings.temp_planning,
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
            f"[Stage 2 – Planning] {timestamp} | "
            f"input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens}"
        )

        # Parse tiered action lists
        quick_wins = _extract_section_items(raw_output, "QUICK WINS")
        medium_term = _extract_section_items(raw_output, "MEDIUM-TERM ACTIONS")
        long_term = _extract_section_items(raw_output, "LONG-TERM INTEGRATION")

        # Equity checklist – look for "EQUITY" keyword section
        equity_checklist = _extract_section_items(raw_output, "EQUITY")

        return ImplementationRoadmap(
            idea=idea,
            quick_wins=quick_wins,
            medium_term=medium_term,
            long_term=long_term,
            equity_checklist=equity_checklist,
            raw_output=raw_output,
        )

    except Exception as exc:  # noqa: BLE001
        ts = datetime.now(tz=timezone.utc).isoformat()
        error_msg = f"Agent failed: {exc}"
        print(f"[Stage 2 – Planning] ERROR at {ts}: {exc}")
        return ImplementationRoadmap(
            idea=idea,
            quick_wins=["Error"],
            medium_term=["Error"],
            long_term=["Error"],
            equity_checklist=[],
            raw_output=error_msg,
        )
