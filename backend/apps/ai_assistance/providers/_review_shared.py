"""Shared decision-review schema and output-cleaning logic for LLM-backed providers.

Every LLM provider (Anthropic, OpenAI, Gemini, ...) asks its model to return
the same structured shape and is held to the same safety rule: only reference
option/evidence/assumption/risk/decision IDs that actually appear in the
snapshot handed to it. Keeping the schema and cleaning logic here means each
provider file only has to own its own API call.
"""

from __future__ import annotations

from typing import Any

from .base import AIReviewOutput, ReviewFinding, SimilarDecision

FINDING_KEYS = (
    "missing_evidence",
    "unsupported_assumptions",
    "contradictory_evidence",
    "duplicate_evidence",
    "missing_stakeholders",
    "risk_highlights",
    "review_triggers",
)

SEVERITIES = {"low", "medium", "high"}

REVIEW_TOOL_NAME = "submit_decision_review"

FINDING_SCHEMA = {
    "type": "object",
    "properties": {
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "title": {"type": "string"},
        "detail": {"type": "string"},
        "related_type": {"type": "string"},
        "related_id": {"type": "string"},
    },
    "required": ["severity", "title", "detail"],
}

REVIEW_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "missing_evidence": {"type": "array", "items": FINDING_SCHEMA},
        "unsupported_assumptions": {"type": "array", "items": FINDING_SCHEMA},
        "contradictory_evidence": {"type": "array", "items": FINDING_SCHEMA},
        "duplicate_evidence": {"type": "array", "items": FINDING_SCHEMA},
        "missing_stakeholders": {"type": "array", "items": FINDING_SCHEMA},
        "risk_highlights": {"type": "array", "items": FINDING_SCHEMA},
        "review_triggers": {"type": "array", "items": FINDING_SCHEMA},
        "similar_decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "decision_id": {"type": "string"},
                    "similarity": {"type": "number"},
                    "reason": {"type": "string"},
                },
                "required": ["decision_id", "similarity", "reason"],
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "summary",
        "missing_evidence",
        "unsupported_assumptions",
        "contradictory_evidence",
        "duplicate_evidence",
        "missing_stakeholders",
        "risk_highlights",
        "review_triggers",
        "similar_decisions",
        "limitations",
    ],
}

REVIEW_TOOL_DESCRIPTION = (
    "Submit a structured advisory review of a governed organisational decision."
)

SYSTEM_PROMPT = """You are an advisory review assistant embedded in an organisational \
decision-governance tool. You review one decision record and surface gaps, \
contradictions, and risks for a human to consider.

You are strictly advisory:
- You cannot alter any record, select an option, or make the decision.
- Every finding is a prompt for human judgement, not a conclusion.
- Only reference option/evidence/assumption/risk IDs that literally appear in the \
provided snapshot. Never invent an ID.
- Only reference decision IDs from the supplied "historical_decisions" list when \
naming a similar decision.
- Be concrete and specific to what was actually recorded; do not pad the review \
with generic advice that ignores the data given.

Call the submit_decision_review tool exactly once with your complete review."""


def valid_ids(snapshot: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("options", "evidence", "assumptions", "risks"):
        for item in snapshot.get(key, []):
            ids.add(item["id"])
    return ids


def clean_finding(raw: dict[str, Any], ids: set[str]) -> ReviewFinding | None:
    if not isinstance(raw, dict):
        return None
    title = str(raw.get("title", "")).strip()
    detail = str(raw.get("detail", "")).strip()
    if not title or not detail:
        return None
    raw_severity = str(raw.get("severity", ""))
    severity = raw_severity if raw_severity in SEVERITIES else "medium"
    related_id = str(raw.get("related_id", "")).strip()
    related_type = str(raw.get("related_type", "")).strip() if related_id else ""
    if related_id not in ids:
        related_id = ""
        related_type = ""
    return ReviewFinding(
        severity=severity,
        title=title,
        detail=detail,
        related_type=related_type,
        related_id=related_id,
    )


def clean_similar(
    raw: dict[str, Any], historical_by_id: dict[str, dict[str, Any]]
) -> SimilarDecision | None:
    if not isinstance(raw, dict):
        return None
    decision_id = str(raw.get("decision_id", "")).strip()
    historical = historical_by_id.get(decision_id)
    if not historical:
        return None
    try:
        similarity = float(raw.get("similarity", 0))
    except (TypeError, ValueError):
        similarity = 0.0
    reason = str(raw.get("reason", "")).strip() or "Identified by the AI reviewer as related."
    return SimilarDecision(
        decision_id=decision_id,
        title=historical["title"],
        status=historical["status"],
        similarity=round(max(0.0, min(similarity, 1.0)), 3),
        url=f"/decisions/{decision_id}",
        reason=reason,
    )


def build_review_output(
    *,
    payload: dict[str, Any],
    snapshot: dict[str, Any],
    provider_label: str,
) -> AIReviewOutput:
    """Turn a raw (untrusted) model payload into a sanitised AIReviewOutput."""
    ids = valid_ids(snapshot)
    findings: dict[str, list[ReviewFinding]] = {}
    for key in FINDING_KEYS:
        findings[key] = [
            cleaned_finding
            for raw in payload.get(key, [])
            if (cleaned_finding := clean_finding(raw, ids)) is not None
        ]

    historical_by_id = {item["id"]: item for item in snapshot.get("historical_decisions", [])}
    similar_decisions = [
        cleaned_similar
        for raw in payload.get("similar_decisions", [])
        if (cleaned_similar := clean_similar(raw, historical_by_id)) is not None
    ]
    similar_decisions.sort(key=lambda item: (-item.similarity, item.title))

    limitations = [
        str(item).strip() for item in payload.get("limitations", []) if str(item).strip()
    ]
    limitations.append(
        f"This review was generated by a large language model ({provider_label}) and "
        "may miss or misjudge context; it does not alter any decision record."
    )

    return AIReviewOutput(
        summary=str(payload.get("summary", "")).strip(),
        missing_evidence=findings["missing_evidence"],
        unsupported_assumptions=findings["unsupported_assumptions"],
        contradictory_evidence=findings["contradictory_evidence"],
        duplicate_evidence=findings["duplicate_evidence"],
        missing_stakeholders=findings["missing_stakeholders"],
        risk_highlights=findings["risk_highlights"],
        review_triggers=findings["review_triggers"],
        similar_decisions=similar_decisions[:5],
        limitations=limitations,
    )


def review_user_message(snapshot: dict[str, Any]) -> str:
    import json

    return "Review this decision record (JSON snapshot):\n\n" + json.dumps(snapshot, default=str)
