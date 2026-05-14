"""
schemas.py – Pydantic v2 data models for the entire pipeline.
"""
from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------

class EvalWeights(BaseModel):
    """Evaluation criteria weights, each on a 0–10 scale."""

    effectiveness: float = Field(default=5.0, ge=0.0, le=10.0)
    efficiency: float = Field(default=5.0, ge=0.0, le=10.0)
    equity: float = Field(default=5.0, ge=0.0, le=10.0)
    liberty: float = Field(default=5.0, ge=0.0, le=10.0)
    political_feasibility: float = Field(default=5.0, ge=0.0, le=10.0)
    social_acceptability: float = Field(default=5.0, ge=0.0, le=10.0)
    administrative_feasibility: float = Field(default=5.0, ge=0.0, le=10.0)


class IdeaInput(BaseModel):
    """Top-level request payload from the frontend."""

    idea: str = Field(..., min_length=10, description="The policy idea to evaluate.")
    mode: Literal["mvp", "full"] = Field(
        default="mvp",
        description="'mvp' runs stages 1, 2, 4. 'full' runs all 5 stages.",
    )
    weights: EvalWeights = Field(default_factory=EvalWeights)


# ---------------------------------------------------------------------------
# Stage output models
# ---------------------------------------------------------------------------

class AssessmentReport(BaseModel):
    """Stage 1 – Idea Assessment Agent output."""

    idea: str
    alignment_finding: str
    conflict_finding: str
    equity_finding: str
    feasibility_finding: str
    implementation_pathway: str
    overall_verdict: str
    raw_output: str
    citations: list[str] = Field(default_factory=list)


class ImplementationRoadmap(BaseModel):
    """Stage 2 – Implementation Planning Agent output."""

    idea: str
    quick_wins: list[str] = Field(default_factory=list)
    medium_term: list[str] = Field(default_factory=list)
    long_term: list[str] = Field(default_factory=list)
    equity_checklist: list[str] = Field(default_factory=list)
    raw_output: str


class EvaluatorFeedback(BaseModel):
    """Stage 3a / 3b / 3c – Individual evaluator output."""

    agent_name: str
    findings: dict[str, str] = Field(default_factory=dict)
    raw_output: str


class SynthesisReport(BaseModel):
    """Stage 5 – Synthesis Agent output."""

    consensus_concerns: list[str] = Field(default_factory=list)
    divergent_concerns: list[str] = Field(default_factory=list)
    priority_revisions: list[str] = Field(default_factory=list)
    overall_readiness: str
    raw_output: str


class PolicyMemo(BaseModel):
    """Stage 4 – Policy Memo Agent output."""

    to_recipient: str
    cc_recipient: str
    date: str = Field(default_factory=lambda: date.today().isoformat())
    re_subject: str
    issue: str
    background: str
    key_findings: list[str] = Field(default_factory=list)
    recommendation: str
    next_steps: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    word_count: int = 0
    raw_output: str


# ---------------------------------------------------------------------------
# Pipeline response model
# ---------------------------------------------------------------------------

class PipelineResult(BaseModel):
    """Complete response returned by POST /api/run."""

    mode: Literal["mvp", "full"]
    idea: str
    stage1: Optional[AssessmentReport] = None
    stage2: Optional[ImplementationRoadmap] = None
    stage3a: Optional[EvaluatorFeedback] = None
    stage3b: Optional[EvaluatorFeedback] = None
    stage3c: Optional[EvaluatorFeedback] = None
    stage4: Optional[PolicyMemo] = None
    stage5: Optional[SynthesisReport] = None
    error: Optional[str] = None
