"""Small, explainable organisational decision metrics."""

from __future__ import annotations

from collections import Counter
from datetime import timedelta
from statistics import median
from typing import Any

from django.utils import timezone

from apps.decisions.models import Decision, DecisionTransition
from apps.lessons.models import Lesson
from apps.organisations.models import Organisation
from apps.participants.models import Participant
from apps.reviews.models import DecisionReview


OPEN_STATUSES = {
    Decision.Status.DRAFT,
    Decision.Status.FRAMING,
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
    Decision.Status.READY_FOR_DECISION,
}
FINALISED_STATUSES = {
    Decision.Status.DECISION_FINALISED,
    Decision.Status.COMMITMENT,
    Decision.Status.IMPLEMENTATION,
    Decision.Status.OUTCOME_REVIEW,
    Decision.Status.LESSONS_LEARNED,
    Decision.Status.ARCHIVED,
}


def organisation_analytics(*, organisation: Organisation) -> dict[str, Any]:
    """Compute decision-flow metrics directly from PostgreSQL-backed records."""
    now = timezone.now()
    today = timezone.localdate()
    decisions = list(
        Decision.objects.filter(organisation=organisation).only(
            "id",
            "status",
            "target_decision_date",
            "created_at",
            "updated_at",
        )
    )
    status_counts = Counter(item.status for item in decisions)
    open_decisions = [item for item in decisions if item.status in OPEN_STATUSES]
    overdue_decisions = [
        item
        for item in open_decisions
        if item.target_decision_date and item.target_decision_date < today
    ]
    created_last_90_days = sum(
        1 for item in decisions if item.created_at >= now - timedelta(days=90)
    )

    finalisation_transitions = DecisionTransition.objects.filter(
        organisation=organisation,
        to_status=Decision.Status.DECISION_FINALISED,
    ).select_related("decision")
    cycle_days = [
        max((transition.created_at - transition.decision.created_at).days, 0)
        for transition in finalisation_transitions
    ]
    median_cycle_days = round(float(median(cycle_days)), 1) if cycle_days else None
    finalised_last_90_days = sum(
        1
        for transition in finalisation_transitions
        if transition.created_at >= now - timedelta(days=90)
    )

    active_participant_counts = Counter(
        str(item["decision_id"])
        for item in Participant.objects.filter(
            organisation=organisation,
            status=Participant.Status.ACTIVE,
        ).values("decision_id")
    )
    contribution_ready = sum(
        1 for item in open_decisions if active_participant_counts[str(item.id)] >= 2
    )
    contribution_coverage = (
        round(contribution_ready / len(open_decisions) * 100, 1)
        if open_decisions
        else None
    )

    reviews = list(
        DecisionReview.objects.filter(organisation=organisation).only(
            "review_due_date",
            "reviewed_at",
            "outcome_assessment",
        )
    )
    due_reviews = [
        item
        for item in reviews
        if item.reviewed_at is None and item.review_due_date <= today
    ]
    outcome_counts = Counter(
        item.outcome_assessment for item in reviews if item.outcome_assessment
    )
    reviewed_outcomes = sum(outcome_counts.values())
    positive_outcomes = outcome_counts["exceeded"] + outcome_counts["met"]
    outcome_success_rate = (
        round(positive_outcomes / reviewed_outcomes * 100, 1)
        if reviewed_outcomes
        else None
    )

    active_lessons = Lesson.objects.filter(
        organisation=organisation,
        status=Lesson.Status.ACTIVE,
    ).count()
    archived_decisions = status_counts[Decision.Status.ARCHIVED]
    finalised_total = sum(status_counts[status] for status in FINALISED_STATUSES)

    return {
        "generated_at": now,
        "totals": {
            "decisions": len(decisions),
            "open_decisions": len(open_decisions),
            "finalised_decisions": finalised_total,
            "archived_decisions": archived_decisions,
            "active_lessons": active_lessons,
        },
        "flow": {
            "status_counts": [
                {
                    "status": status,
                    "label": Decision.Status(status).label,
                    "count": status_counts[status],
                }
                for status, _label in Decision.Status.choices
            ],
            "created_last_90_days": created_last_90_days,
            "finalised_last_90_days": finalised_last_90_days,
            "median_days_to_finalise": median_cycle_days,
            "overdue_target_decisions": len(overdue_decisions),
            "contribution_coverage_percent": contribution_coverage,
        },
        "learning": {
            "outcome_reviews_completed": reviewed_outcomes,
            "outcome_success_percent": outcome_success_rate,
            "outcome_assessment_counts": [
                {
                    "assessment": assessment,
                    "label": DecisionReview.OutcomeAssessment(assessment).label,
                    "count": outcome_counts[assessment],
                }
                for assessment, _label in DecisionReview.OutcomeAssessment.choices
            ],
            "reviews_due_or_overdue": len(due_reviews),
            "active_lessons": active_lessons,
        },
        "definitions": {
            "median_days_to_finalise": (
                "Median calendar days from decision creation to the recorded "
                "human finalisation transition."
            ),
            "contribution_coverage_percent": (
                "Share of open decisions with at least two active participants."
            ),
            "outcome_success_percent": (
                "Share of completed outcome reviews assessed as met or "
                "exceeded expectations."
            ),
        },
    }
