"""Tenant-safe selectors for execution and outcome records."""

from __future__ import annotations

from uuid import UUID

from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user

from .models import DecisionReview


def review_for_user(*, user: User, decision_id: UUID) -> DecisionReview | None:
    """Return the review only after tenant access has been established."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return (
        DecisionReview.objects.select_related(
            "decision",
            "organisation",
            "implementation_owner",
            "commitment_recorded_by",
            "implementation_started_by",
            "reviewed_by",
        )
        .filter(decision=decision)
        .first()
    )


def required_review_for_user(*, user: User, decision_id: UUID) -> DecisionReview:
    decision = decision_for_user(user=user, decision_id=decision_id)
    return get_object_or_404(
        DecisionReview.objects.select_related(
            "decision",
            "organisation",
            "implementation_owner",
            "commitment_recorded_by",
            "implementation_started_by",
            "reviewed_by",
        ),
        decision=decision,
    )
