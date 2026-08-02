"""Provider-neutral contracts for AI decision review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ReviewFinding:
    severity: str
    title: str
    detail: str
    related_type: str = ""
    related_id: str = ""


@dataclass(frozen=True)
class SimilarDecision:
    decision_id: str
    title: str
    status: str
    similarity: float
    url: str
    reason: str


@dataclass(frozen=True)
class AIReviewOutput:
    summary: str
    missing_evidence: list[ReviewFinding] = field(default_factory=list)
    unsupported_assumptions: list[ReviewFinding] = field(default_factory=list)
    contradictory_evidence: list[ReviewFinding] = field(default_factory=list)
    missing_stakeholders: list[ReviewFinding] = field(default_factory=list)
    risk_highlights: list[ReviewFinding] = field(default_factory=list)
    similar_decisions: list[SimilarDecision] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class AIProvider(Protocol):
    """Replaceable provider contract. Providers may use rules, local models, or APIs."""

    key: str
    label: str
    model_identifier: str

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        """Return advisory output without mutating any organisational record."""
