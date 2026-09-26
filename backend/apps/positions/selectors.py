"""Tenant-safe stakeholder position selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.db.models import OuterRef, Subquery

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user
from apps.participants.models import Participant

from .models import Position


def _with_related(queryset: models.QuerySet[Position]) -> models.QuerySet[Position]:
    return queryset.select_related(
        "participant__user",
        "preferred_option",
        "submitted_by",
    )


def current_positions_queryset(  # type: ignore[no-untyped-def]
    *, decision
) -> models.QuerySet[Position]:
    """Return the latest immutable position for each active participant."""
    latest_version = (
        Position.objects.filter(
            decision=decision,
            participant_id=OuterRef("participant_id"),
        )
        .order_by("-version")
        .values("version")[:1]
    )
    return _with_related(
        Position.objects.filter(
            decision=decision,
            participant__status=Participant.Status.ACTIVE,
            version=Subquery(latest_version),
        )
    )


def current_positions_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Position]:
    """Return current positions only after resolving tenant visibility."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return current_positions_queryset(decision=decision)


def position_history_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Position]:
    """Return all position versions after resolving tenant visibility."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return _with_related(Position.objects.filter(decision=decision))
