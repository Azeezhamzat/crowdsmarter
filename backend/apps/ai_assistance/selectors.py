"""Tenant-safe AI review selectors."""

from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user

from .models import AIReview


def reviews_for_decision(
    *, user: User, decision_id: UUID
) -> QuerySet[AIReview]:
    decision = decision_for_user(user=user, decision_id=decision_id)
    return AIReview.objects.filter(decision=decision).select_related(
        "requested_by", "reviewed_by", "dismissed_by", "decision"
    )


def review_for_user(*, user: User, review_id: UUID) -> AIReview:
    return get_object_or_404(
        AIReview.objects.select_related(
            "decision__organisation",
            "decision__owner",
            "requested_by",
            "reviewed_by",
            "dismissed_by",
        ).filter(
            organisation__memberships__user=user,
            organisation__memberships__status="active",
        ),
        id=review_id,
    )
