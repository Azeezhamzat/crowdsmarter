"""Decision overview read model for a coherent executive workspace."""

from __future__ import annotations

from django.db.models import Count, F, Q
from django.utils import timezone

from apps.collaboration.models import DiscussionEntry
from apps.decision_options.models import DecisionOption
from apps.decision_options.services import budget_summary
from apps.foresight.models import SignalDecisionLink, StrategicImplication
from apps.participants.models import Participant
from apps.risks.models import Risk

from .models import Decision
from .reasoning import reasoning_summary

STATUS_ORDER = [value for value, _ in Decision.Status.choices]


def _display_name(user) -> str:  # type: ignore[no-untyped-def]
    full_name = f"{user.first_name} {user.last_name}".strip()
    return full_name or user.email


def _next_action(decision: Decision, blockers: list[str], unresolved: int) -> dict:
    if decision.status == Decision.Status.DRAFT:
        missing = [
            label
            for value, label in (
                (decision.decision_question, "decision question"),
                (decision.purpose, "purpose"),
                (decision.scope, "scope"),
            )
            if not value
        ]
        if missing:
            return {
                "label": "Complete the decision frame",
                "description": f"Add {', '.join(missing)} before moving into framing.",
                "route": f"/decisions/{decision.id}#framing",
            }
        return {
            "label": "Move into framing",
            "description": (
                "The core frame is present. Review it and record why formal framing should begin."
            ),
            "route": f"/decisions/{decision.id}#lifecycle",
        }
    if decision.status == Decision.Status.FRAMING:
        return {
            "label": "Prepare stakeholder contribution",
            "description": (
                "Set contribution boundaries and a future deadline, then confirm "
                "the right participants."
            ),
            "route": f"/decisions/{decision.id}#participants",
        }
    if decision.status == Decision.Status.OPEN_FOR_CONTRIBUTION:
        return {
            "label": "Build the reasoning record",
            "description": (
                "Develop options, evidence, assumptions, risks, and resolve material questions."
            ),
            "route": f"/decisions/{decision.id}/reasoning/options",
        }
    if decision.status == Decision.Status.UNDER_REVIEW:
        if blockers:
            return {
                "label": "Resolve readiness blockers",
                "description": blockers[0],
                "route": f"/decisions/{decision.id}/reasoning/options",
            }
        if unresolved:
            return {
                "label": "Resolve open questions and concerns",
                "description": (
                    f"{unresolved} unresolved discussion item(s) still need an explicit response."
                ),
                "route": f"/decisions/{decision.id}/collaboration",
            }
        return {
            "label": "Confirm readiness for decision",
            "description": (
                "The minimum reasoning gate is met. Human reviewers should judge "
                "sufficiency before advancing."
            ),
            "route": f"/decisions/{decision.id}#lifecycle",
        }
    if decision.status == Decision.Status.READY_FOR_DECISION:
        return {
            "label": "Record stakeholder positions",
            "description": (
                "Required decision authorities must submit current positions before "
                "human finalisation."
            ),
            "route": f"/decisions/{decision.id}/governance",
        }
    if decision.status == Decision.Status.DECISION_FINALISED:
        return {
            "label": "Record implementation commitment",
            "description": (
                "Assign accountable implementation ownership, success measures, "
                "and an outcome-review date."
            ),
            "route": f"/decisions/{decision.id}/outcomes",
        }
    if decision.status in {Decision.Status.COMMITMENT, Decision.Status.IMPLEMENTATION}:
        return {
            "label": "Maintain implementation accountability",
            "description": (
                "Keep the implementation record current and prepare attributable outcome evidence."
            ),
            "route": f"/decisions/{decision.id}/outcomes",
        }
    if decision.status in {Decision.Status.OUTCOME_REVIEW, Decision.Status.LESSONS_LEARNED}:
        return {
            "label": "Complete the learning cycle",
            "description": "Assess actual outcomes and capture reusable lessons before archival.",
            "route": f"/decisions/{decision.id}/outcomes",
        }
    return {
        "label": "Review the preserved decision record",
        "description": "This decision is archived and read-only.",
        "route": f"/decisions/{decision.id}",
    }


def decision_overview(decision: Decision) -> dict:
    """Build a concise read model without changing any decision state."""
    reasoning = reasoning_summary(decision)
    participants = list(
        decision.participants.filter(status=Participant.Status.ACTIVE)
        .select_related("user")
        .order_by("role", "user__email")
    )
    role_counts = {
        row["role"]: row["count"]
        for row in decision.participants.filter(status=Participant.Status.ACTIVE)
        .values("role")
        .annotate(count=Count("id"))
    }
    unresolved = DiscussionEntry.objects.filter(
        decision=decision,
        kind__in=[DiscussionEntry.Kind.QUESTION, DiscussionEntry.Kind.CONCERN],
        resolved_at__isnull=True,
    ).count()
    options = list(
        DecisionOption.objects.filter(
            decision=decision,
            status=DecisionOption.Status.ACTIVE,
        )
        .annotate(
            evidence_count=Count("evidence_items", distinct=True),
            risk_count=Count("risks", filter=~Q(risks__status=Risk.Status.CLOSED), distinct=True),
        )
        .values("id", "title", "is_status_quo", "evidence_count", "risk_count")[:6]
    )
    linked_signals = [
        {
            "id": str(link.signal_id),
            "title": link.signal.title,
            "steep_category": link.signal.steep_category,
            "time_horizon": link.signal.time_horizon,
            "maturity": link.signal.maturity,
            "priority_score": link.signal.priority_score,
            "relevance": link.relevance,
        }
        for link in SignalDecisionLink.objects.filter(decision=decision)
        .select_related("signal")
        .order_by("-signal__impact", "-signal__uncertainty", "-created_at")[:6]
    ]
    foresight_implications = [
        {
            "id": str(item.id),
            "canvas_id": str(item.canvas_id),
            "canvas_title": item.canvas.title,
            "title": item.title,
            "description": item.description,
            "implication_type": item.implication_type,
            "priority": item.priority,
            "status": item.status,
            "owner": _display_name(item.owner),
        }
        for item in StrategicImplication.objects.filter(linked_decision=decision)
        .select_related("canvas", "owner")
        .order_by("-priority", "title")[:6]
    ]
    risks = [
        {
            "id": str(risk.id),
            "title": risk.title,
            "score": risk.score,
            "status": risk.status,
            "owner": _display_name(risk.owner),
        }
        for risk in Risk.objects.filter(decision=decision)
        .exclude(status=Risk.Status.CLOSED)
        .select_related("owner")
        .annotate(risk_score=F("likelihood") * F("impact"))
        .order_by("-risk_score", "-impact", "title")[:4]
    ]
    stage_index = STATUS_ORDER.index(decision.status)
    today = timezone.localdate()
    is_overdue = bool(
        decision.target_decision_date
        and decision.target_decision_date < today
        and decision.status
        not in {
            Decision.Status.DECISION_FINALISED,
            Decision.Status.COMMITMENT,
            Decision.Status.IMPLEMENTATION,
            Decision.Status.OUTCOME_REVIEW,
            Decision.Status.LESSONS_LEARNED,
            Decision.Status.ARCHIVED,
        }
    )
    return {
        "progress": {
            "stage_index": stage_index,
            "stage_count": len(STATUS_ORDER),
            "percent": round((stage_index / (len(STATUS_ORDER) - 1)) * 100),
        },
        "next_action": _next_action(decision, reasoning["blockers"], unresolved),
        "framing": {
            "completed": sum(
                bool(value)
                for value in (
                    decision.decision_question,
                    decision.purpose,
                    decision.context,
                    decision.scope,
                    decision.contribution_guidance,
                )
            ),
            "total": 5,
            "missing": [
                label
                for value, label in (
                    (decision.decision_question, "Decision question"),
                    (decision.purpose, "Purpose"),
                    (decision.context, "Context"),
                    (decision.scope, "Scope"),
                    (decision.contribution_guidance, "Contribution boundaries"),
                )
                if not value
            ],
        },
        "participants": {
            "total": len(participants),
            "role_counts": role_counts,
            "people": [
                {
                    "id": str(item.id),
                    "name": _display_name(item.user),
                    "email": item.user.email,
                    "role": item.role,
                    "role_label": item.get_role_display(),
                }
                for item in participants
            ],
        },
        "discussion": {"unresolved": unresolved},
        "budget": budget_summary(decision=decision)
        if decision.source_template_key == "grant_round"
        else None,
        "options": options,
        "material_risks": risks,
        "linked_signals": linked_signals,
        "foresight_implications": foresight_implications,
        "reasoning": reasoning,
        "target": {
            "date": decision.target_decision_date,
            "is_overdue": is_overdue,
        },
    }
