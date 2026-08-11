"""Shared analytics-narrative schema and output-cleaning logic for LLM-backed providers."""

from __future__ import annotations

import json
from typing import Any

from .base import AnalyticsNarrative, AnalyticsObservation

SEVERITIES = {"low", "medium", "high"}

NARRATIVE_TOOL_NAME = "submit_analytics_narrative"

OBSERVATION_SCHEMA = {
    "type": "object",
    "properties": {
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "title": {"type": "string"},
        "detail": {"type": "string"},
    },
    "required": ["severity", "title", "detail"],
}

NARRATIVE_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "headline": {"type": "string"},
        "observations": {"type": "array", "items": OBSERVATION_SCHEMA},
    },
    "required": ["headline", "observations"],
}

NARRATIVE_TOOL_DESCRIPTION = (
    "Submit a short, evidence-grounded narrative over an organisation's decision-system metrics."
)

SYSTEM_PROMPT = """You are an analytics narrator embedded in an organisational decision-governance \
tool. You are given a small set of explainable, already-computed decision-system metrics \
(counts, percentages, medians) for one organisation and must turn them into a short, plain-language \
narrative a busy executive can read in ten seconds.

Rules:
- Only state what the numbers actually show. Never invent a figure, trend, or comparison that \
is not present in the supplied metrics.
- Do not moralise or pad with generic advice ("communication is important"). Be concrete and \
specific to the numbers given.
- Prefer noting genuine risk signals (overdue items, low coverage, stalled cycle time) over \
restating totals.
- If a metric is null (not enough data yet), do not treat that as bad news; simply omit it or \
note that there is not yet enough data.
- This narrative is advisory only. It does not alter any record and does not judge any specific \
decision or person.

Call the submit_analytics_narrative tool exactly once with your complete narrative."""


def clean_observation(raw: dict[str, Any]) -> AnalyticsObservation | None:
    if not isinstance(raw, dict):
        return None
    title = str(raw.get("title", "")).strip()
    detail = str(raw.get("detail", "")).strip()
    if not title or not detail:
        return None
    severity = raw.get("severity") if raw.get("severity") in SEVERITIES else "medium"
    return AnalyticsObservation(severity=severity, title=title, detail=detail)


def build_narrative(*, payload: dict[str, Any], provider_label: str) -> AnalyticsNarrative:
    headline = str(payload.get("headline", "")).strip() or "No headline was returned."
    observations = [
        cleaned
        for raw in payload.get("observations", [])
        if (cleaned := clean_observation(raw)) is not None
    ]
    return AnalyticsNarrative(headline=headline, observations=observations, generated_by=provider_label)


def narrative_user_message(metrics: dict[str, Any]) -> str:
    return "Summarise these organisation decision-system metrics (JSON):\n\n" + json.dumps(metrics, default=str)
