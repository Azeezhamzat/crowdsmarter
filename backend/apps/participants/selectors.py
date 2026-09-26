"""Tenant-safe participant selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user

from .models import ConflictOfInterest, Participant


def participants_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Participant]:
    """List active participants after establishing decision access."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return Participant.objects.filter(
        decision=decision,
        status=Participant.Status.ACTIVE,
    ).select_related("user", "added_by")


def participant_for_user(*, user: User, participant_id: UUID) -> Participant:
    """Fetch a participant without revealing another tenant's records."""
    return get_object_or_404(
        Participant.objects.select_related(
            "decision", "decision__organisation", "user", "added_by"
        ).filter(decision__organisation__in=user_organisations(user)),
        id=participant_id,
        status=Participant.Status.ACTIVE,
    )


def user_organisations(user: User):  # type: ignore[no-untyped-def]
    """Return organisation scope without importing a private selector."""
    from apps.organisations.models import Organisation

    return Organisation.objects.for_user(user)


def conflict_for_user(*, user: User, conflict_id: UUID) -> ConflictOfInterest:
    """Fetch a conflict declaration without revealing another tenant's records."""
    return get_object_or_404(
        ConflictOfInterest.objects.select_related(
            "participant__decision",
            "participant__decision__organisation",
            "participant__user",
            "option",
        ).filter(organisation__in=user_organisations(user)),
        id=conflict_id,
    )
