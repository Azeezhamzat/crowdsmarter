"""Deterministic decision snapshots supplied to replaceable AI providers."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from django.utils import timezone

from apps.assumptions.models import Assumption
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.evidence.models import Evidence
from apps.lessons.models import Lesson
from apps.participants.models import Participant
from apps.risks.models import Risk


def _json_ready(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, (UUID, Decimal, Enum)):
        return str(value.value if isinstance(value, Enum) else value)
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_ready(item) for item in value]
    return str(value)


def build_decision_snapshot(*, decision: Decision) -> dict[str, Any]:
    options = list(
        DecisionOption.objects.filter(
            decision=decision,
            status=DecisionOption.Status.ACTIVE,
        ).values(
            "id",
            "title",
            "description",
            "expected_benefits",
            "tradeoffs",
            "is_status_quo",
            "updated_at",
        )
    )
    evidence = list(
        Evidence.objects.filter(
            decision=decision,
            status=Evidence.Status.ACTIVE,
        ).values(
            "id",
            "option_id",
            "title",
            "summary",
            "source_type",
            "source_reference",
            "source_url",
            "stance",
            "strength",
            "updated_at",
        )
    )
    assumptions = list(
        Assumption.objects.filter(
            decision=decision,
            status=Assumption.Status.ACTIVE,
        ).values(
            "id",
            "option_id",
            "statement",
            "rationale",
            "impact_if_false",
            "confidence",
            "verification_status",
            "verification_notes",
            "owner_id",
            "review_date",
            "updated_at",
        )
    )
    risks = list(
        Risk.objects.filter(decision=decision).exclude(
            status=Risk.Status.CLOSED
        ).values(
            "id",
            "option_id",
            "title",
            "description",
            "likelihood",
            "impact",
            "response_strategy",
            "mitigation_plan",
            "owner_id",
            "review_date",
            "status",
            "updated_at",
        )
    )
    participants = list(
        Participant.objects.filter(
            decision=decision,
            status=Participant.Status.ACTIVE,
        ).values("id", "user_id", "role", "updated_at")
    )
    historical_decisions = []
    prior = (
        Decision.objects.filter(organisation=decision.organisation)
        .exclude(id=decision.id)
        .exclude(status__in=[Decision.Status.DRAFT, Decision.Status.FRAMING])
        .order_by("-updated_at")[:50]
    )
    lessons_by_decision: dict[str, list[str]] = {}
    for lesson in Lesson.objects.filter(
        decision_id__in=[item.id for item in prior],
        status=Lesson.Status.ACTIVE,
    ).values("decision_id", "title"):
        lessons_by_decision.setdefault(str(lesson["decision_id"]), []).append(
            lesson["title"]
        )
    for item in prior:
        historical_decisions.append(
            {
                "id": str(item.id),
                "title": item.title,
                "decision_question": item.decision_question,
                "purpose": item.purpose,
                "context": item.context,
                "status": item.status,
                "lesson_titles": lessons_by_decision.get(str(item.id), []),
                "updated_at": item.updated_at,
            }
        )
    snapshot = {
        "schema_version": "decision-snapshot-v1",
        "generated_at": timezone.now(),
        "decision": {
            "id": str(decision.id),
            "organisation_id": str(decision.organisation_id),
            "title": decision.title,
            "decision_question": decision.decision_question,
            "purpose": decision.purpose,
            "context": decision.context,
            "scope": decision.scope,
            "contribution_guidance": decision.contribution_guidance,
            "urgency": decision.urgency,
            "target_decision_date": decision.target_decision_date,
            "status": decision.status,
            "owner_id": str(decision.owner_id),
            "updated_at": decision.updated_at,
        },
        "options": options,
        "evidence": evidence,
        "assumptions": assumptions,
        "risks": risks,
        "participants": participants,
        "historical_decisions": historical_decisions,
    }
    return _json_ready(snapshot)
