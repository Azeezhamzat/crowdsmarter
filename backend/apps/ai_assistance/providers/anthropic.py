"""Real-model decision review via the Anthropic API.

Produces the exact same AIReviewOutput shape as the rules provider, so the
rest of the app (storage, display, human review/dismissal, quality metrics)
is completely provider-agnostic. The model is explicitly instructed to stay
advisory only, mirroring the constraint the rules provider already
satisfies structurally: it can surface findings, it cannot alter records,
choose an option, or exercise decision authority.
"""

from __future__ import annotations

import json
from typing import Any

import anthropic

from apps.platform_admin.crypto import decrypt_secret
from apps.platform_admin.models import PlatformConfiguration

from .base import AIReviewOutput, ReviewFinding, SimilarDecision

_FINDING_KEYS = (
    "missing_evidence",
    "unsupported_assumptions",
    "contradictory_evidence",
    "duplicate_evidence",
    "missing_stakeholders",
    "risk_highlights",
    "review_triggers",
)

_SEVERITIES = {"low", "medium", "high"}

_REVIEW_TOOL_NAME = "submit_decision_review"

_FINDING_SCHEMA = {
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

_REVIEW_TOOL = {
    "name": _REVIEW_TOOL_NAME,
    "description": (
        "Submit a structured advisory review of a governed organisational decision."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "summary": {"type": "string"},
            "missing_evidence": {"type": "array", "items": _FINDING_SCHEMA},
            "unsupported_assumptions": {"type": "array", "items": _FINDING_SCHEMA},
            "contradictory_evidence": {"type": "array", "items": _FINDING_SCHEMA},
            "duplicate_evidence": {"type": "array", "items": _FINDING_SCHEMA},
            "missing_stakeholders": {"type": "array", "items": _FINDING_SCHEMA},
            "risk_highlights": {"type": "array", "items": _FINDING_SCHEMA},
            "review_triggers": {"type": "array", "items": _FINDING_SCHEMA},
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
    },
}

_SYSTEM_PROMPT = """You are an advisory review assistant embedded in an organisational \
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


def _valid_ids(snapshot: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for key in ("options", "evidence", "assumptions", "risks"):
        for item in snapshot.get(key, []):
            ids.add(item["id"])
    return ids


def _clean_finding(raw: dict[str, Any], valid_ids: set[str]) -> ReviewFinding | None:
    if not isinstance(raw, dict):
        return None
    title = str(raw.get("title", "")).strip()
    detail = str(raw.get("detail", "")).strip()
    if not title or not detail:
        return None
    severity = raw.get("severity") if raw.get("severity") in _SEVERITIES else "medium"
    related_id = str(raw.get("related_id", "")).strip()
    related_type = str(raw.get("related_type", "")).strip() if related_id else ""
    if related_id not in valid_ids:
        related_id = ""
        related_type = ""
    return ReviewFinding(
        severity=severity,
        title=title,
        detail=detail,
        related_type=related_type,
        related_id=related_id,
    )


def _clean_similar(raw: dict[str, Any], historical_by_id: dict[str, dict[str, Any]]) -> SimilarDecision | None:
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


class AnthropicAIProvider:
    """Real-LLM decision review backed by the Anthropic Messages API."""

    key = "anthropic"
    label = "Anthropic Claude"

    def __init__(self) -> None:
        config = PlatformConfiguration.load()
        if not config.ai_provider_api_key_is_set:
            raise ValueError(
                "No Anthropic API key is configured. Set one from Platform "
                "Administration before selecting this provider."
            )
        self.model_identifier = config.ai_provider_model.strip() or "claude-sonnet-5"
        self._api_key = decrypt_secret(config.ai_provider_api_key_encrypted)

    def review_decision(self, *, snapshot: dict[str, Any]) -> AIReviewOutput:
        client = anthropic.Anthropic(api_key=self._api_key)
        message = client.messages.create(
            model=self.model_identifier,
            max_tokens=4096,
            system=_SYSTEM_PROMPT,
            tools=[_REVIEW_TOOL],
            tool_choice={"type": "tool", "name": _REVIEW_TOOL_NAME},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Review this decision record (JSON snapshot):\n\n"
                        + json.dumps(snapshot, default=str)
                    ),
                }
            ],
        )
        tool_use = next(
            (block for block in message.content if block.type == "tool_use"),
            None,
        )
        if tool_use is None:
            raise ValueError("The AI provider did not return a structured review.")
        payload: dict[str, Any] = tool_use.input

        valid_ids = _valid_ids(snapshot)
        findings: dict[str, list[ReviewFinding]] = {}
        for key in _FINDING_KEYS:
            findings[key] = [
                cleaned
                for raw in payload.get(key, [])
                if (cleaned := _clean_finding(raw, valid_ids)) is not None
            ]

        historical_by_id = {item["id"]: item for item in snapshot.get("historical_decisions", [])}
        similar_decisions = [
            cleaned
            for raw in payload.get("similar_decisions", [])
            if (cleaned := _clean_similar(raw, historical_by_id)) is not None
        ]
        similar_decisions.sort(key=lambda item: (-item.similarity, item.title))

        limitations = [str(item).strip() for item in payload.get("limitations", []) if str(item).strip()]
        limitations.append(
            "This review was generated by a large language model and may miss or "
            "misjudge context; it does not alter any decision record."
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
