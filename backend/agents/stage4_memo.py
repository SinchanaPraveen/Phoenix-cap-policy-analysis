"""
stage4_memo.py – Stage 4: Policy Memo Agent.

Calls the Claude API to produce a formal, executive-ready one-page
policy memo synthesising all prior stage outputs. Recipient is
determined automatically from the authority scope detected in the
Stage 2 roadmap.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone

import anthropic

from config import settings
from prompts.stage4 import SYSTEM_PROMPT, USER_TEMPLATE
from schemas import (
    AssessmentReport,
    EvalWeights,
    EvaluatorFeedback,
    ImplementationRoadmap,
    PolicyMemo,
    SynthesisReport,
)

# ---------------------------------------------------------------------------
# Module-level Anthropic client
# ---------------------------------------------------------------------------
client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

# ---------------------------------------------------------------------------
# Recipient lookup table (mirrors RECIPIENT LOGIC in prompt)
# ---------------------------------------------------------------------------
_AUTHORITY_RECIPIENTS: dict[str, tuple[str, str]] = {
    "city-only": (
        "City Manager, City of Phoenix",
        "",
    ),
    "requires state action": (
        "Director, Arizona Department of Environmental Quality",
        "",
    ),
    "requires federal action": (
        "Office of the Mayor, City of Phoenix",
        "",
    ),
    "multi-level": (
        "Office of the Mayor, City of Phoenix",
        "",
    ),
}

_EQUITY_CC = "Director, Office of Equity, City of Phoenix"


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


def _determine_recipient(
    stage2: ImplementationRoadmap,
    stage1: AssessmentReport,
) -> tuple[str, str]:
    """
    Determine the memo TO and CC recipients from the Stage 2 raw output.

    Scans the roadmap text for ``Authority Scope`` labels in priority order:
    ``Requires State Action`` → ``Multi-level`` → ``Requires Federal Action``
    → ``City-only``.  Falls back to ``City-only`` if none found.

    If the Stage 1 equity finding contains ``"Advances"``, adds the equity
    office to the CC line.

    Parameters
    ----------
    stage2:
        Completed :class:`~schemas.ImplementationRoadmap` from Stage 2.
    stage1:
        Completed :class:`~schemas.AssessmentReport` from Stage 1 (used
        to check equity finding for CC logic).

    Returns
    -------
    tuple[str, str]
        ``(to_recipient, cc_recipient)`` strings.
    """
    raw = stage2.raw_output.lower()

    if "requires state action" in raw:
        key = "requires state action"
    elif "multi-level" in raw:
        key = "multi-level"
    elif "requires federal action" in raw:
        key = "requires federal action"
    else:
        key = "city-only"

    to_recipient, cc_recipient = _AUTHORITY_RECIPIENTS[key]

    # Equity CC logic
    if "advances" in stage1.equity_finding.lower():
        cc_recipient = _EQUITY_CC

    return to_recipient, cc_recipient


def _extract_memo_field(text: str, field_label: str) -> str:
    """
    Extract the value of a memo header field (TO, CC, RE, etc.).

    Parameters
    ----------
    text:
        Raw LLM output.
    field_label:
        The header label to match (e.g. ``"TO"``, ``"RE"``).

    Returns
    -------
    str
        The extracted value string, stripped of whitespace.
    """
    pattern = rf"^{re.escape(field_label)}:\s*(.+)$"
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section(text: str, section_label: str, next_label: str = "") -> str:
    """
    Extract a prose section body from the memo between two headers.

    Parameters
    ----------
    text:
        Raw LLM output.
    section_label:
        The heading that starts the section (e.g. ``"ISSUE"``).
    next_label:
        The heading that ends the section; if empty, reads to end of string.

    Returns
    -------
    str
        Stripped section body text.
    """
    end_pattern = rf"(?={re.escape(next_label)})" if next_label else r"\Z"
    pattern = rf"\b{re.escape(section_label)}\b[:\s]*(.*?){end_pattern}"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return " ".join(match.group(1).split()) if match else ""


def _extract_bullet_list(text: str, section_label: str, next_label: str = "") -> list[str]:
    """
    Extract a bulleted/numbered list from a memo section.

    Parameters
    ----------
    text:
        Raw LLM output.
    section_label:
        The heading that starts the section.
    next_label:
        The heading that ends the section; if empty reads to end of string.

    Returns
    -------
    list[str]
        Stripped list of item strings.
    """
    end_pattern = rf"(?={re.escape(next_label)})" if next_label else r"\Z"
    pattern = rf"\b{re.escape(section_label)}\b[:\s]*(.*?){end_pattern}"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if not match:
        return []

    block = match.group(1)
    items: list[str] = []
    for line in block.splitlines():
        stripped = re.sub(r"^[\s\-\*\d\.\)•]+", "", line).strip()
        if stripped:
            items.append(stripped)
    return items


def _extract_citations(text: str) -> list[str]:
    """
    Extract all CAP citations from the memo text.

    Matches patterns like ``CAP Goal H2, p. 151``, ``CAP Strategy SES1``,
    ``CAP p. 42``, etc.

    Parameters
    ----------
    text:
        Raw LLM output.

    Returns
    -------
    list[str]
        Deduplicated list of citation strings, preserving order of first
        occurrence.
    """
    pattern = r"CAP\s+(?:Goal|Strategy|Section|p\.?|Page|Action)?\s*[A-Z0-9][A-Z0-9\-\.,\s]+"
    matches = re.findall(pattern, text, re.IGNORECASE)
    seen: set[str] = set()
    citations: list[str] = []
    for m in matches:
        normalised = " ".join(m.split()).rstrip(",.")
        if normalised not in seen:
            seen.add(normalised)
            citations.append(normalised)
    return citations


# ---------------------------------------------------------------------------
# Main agent function
# ---------------------------------------------------------------------------

def run_stage4(
    idea: str,
    stage1: AssessmentReport,
    stage2: ImplementationRoadmap,
    weights: EvalWeights,
    stage3a: EvaluatorFeedback | None = None,
    stage3b: EvaluatorFeedback | None = None,
    stage3c: EvaluatorFeedback | None = None,
    stage5: SynthesisReport | None = None,
) -> PolicyMemo:
    """Run the Stage 4 Policy Memo Agent.

    Synthesises all prior stage outputs into a formal, executive-ready
    one-page policy memo (400–450 words).  Recipient is determined
    automatically from the authority scope pattern in the Stage 2 roadmap.
    Evaluator and synthesis outputs are optional (MVP mode omits them).

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
    stage3a:
        Optional :class:`~schemas.EvaluatorFeedback` from the Neutral
        Evaluator.  Pass ``None`` in MVP mode.
    stage3b:
        Optional :class:`~schemas.EvaluatorFeedback` from the Phoenix
        Citizen.  Pass ``None`` in MVP mode.
    stage3c:
        Optional :class:`~schemas.EvaluatorFeedback` from the ADEQ
        Analyst.  Pass ``None`` in MVP mode.
    stage5:
        Optional :class:`~schemas.SynthesisReport` from Stage 5.
        Pass ``None`` in MVP mode.

    Returns
    -------
    PolicyMemo
        Parsed policy memo with structured header fields, prose sections,
        bullet lists, CAP citations, and word count.  On API error the
        ``raw_output`` field contains the error message and text fields
        are populated with ``"Error"``.
    """
    weights_block = _build_weights_block(weights)
    weights_json = json.dumps(weights.model_dump(), indent=2)
    current_date = date.today().isoformat()

    system_prompt = SYSTEM_PROMPT.format(
        weights_block=weights_block,
        current_date=current_date,
    )
    user_message = USER_TEMPLATE.format(
        idea=idea,
        stage1_output=stage1.raw_output,
        stage2_output=stage2.raw_output,
        stage3a_output=stage3a.raw_output if stage3a else "",
        stage3b_output=stage3b.raw_output if stage3b else "",
        stage3c_output=stage3c.raw_output if stage3c else "",
        stage5_output=stage5.raw_output if stage5 else "",
        current_date=current_date,
        weights_json=weights_json,
    )

    # Determine recipient before the API call (used as fallback if parsing fails)
    fallback_to, fallback_cc = _determine_recipient(stage2, stage1)

    try:
        response = client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.max_tokens_stage4,
            temperature=settings.temp_memo,
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
            f"[Stage 4 – Policy Memo] {timestamp} | "
            f"input_tokens={usage.input_tokens} "
            f"output_tokens={usage.output_tokens}"
        )

        # Parse memo header fields
        to_recipient = _extract_memo_field(raw_output, "TO") or fallback_to
        cc_recipient = _extract_memo_field(raw_output, "CC") or fallback_cc
        re_subject = _extract_memo_field(raw_output, "RE")

        # Parse prose sections
        issue = _extract_section(raw_output, "ISSUE", "BACKGROUND")
        background = _extract_section(raw_output, "BACKGROUND", "KEY FINDINGS")
        recommendation = _extract_section(raw_output, "RECOMMENDATION", "NEXT STEPS")

        # Parse bullet lists
        key_findings = _extract_bullet_list(raw_output, "KEY FINDINGS", "RECOMMENDATION")
        next_steps = _extract_bullet_list(raw_output, "NEXT STEPS", "ATTACHMENTS")

        # Citations and word count
        citations = _extract_citations(raw_output)
        # Count words in the body (exclude header lines and attachments line)
        body_text = re.sub(r"^(TO|CC|FROM|DATE|RE|ATTACHMENTS):.*$", "", raw_output, flags=re.MULTILINE | re.IGNORECASE)
        word_count = len(body_text.split())

        return PolicyMemo(
            to_recipient=to_recipient,
            cc_recipient=cc_recipient,
            date=current_date,
            re_subject=re_subject or f"Policy Analysis: {idea[:60]}",
            issue=issue,
            background=background,
            key_findings=key_findings,
            recommendation=recommendation,
            next_steps=next_steps,
            citations=citations,
            word_count=word_count,
            raw_output=raw_output,
        )

    except Exception as exc:  # noqa: BLE001
        ts = datetime.now(tz=timezone.utc).isoformat()
        error_msg = f"Agent failed: {exc}"
        print(f"[Stage 4 – Policy Memo] ERROR at {ts}: {exc}")
        return PolicyMemo(
            to_recipient=fallback_to,
            cc_recipient=fallback_cc,
            date=current_date,
            re_subject="Error",
            issue="Error",
            background="Error",
            key_findings=["Error"],
            recommendation="Error",
            next_steps=["Error"],
            citations=[],
            word_count=0,
            raw_output=error_msg,
        )
