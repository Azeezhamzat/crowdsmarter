"""Shared permissions for structured decision reasoning records."""

from __future__ import annotations

from apps.accounts.models import User
from apps.organisations.models import Membership
from apps.participants.models import Participant

from .models import Decision
from .policies import MANAGER_ROLES, active_membership

MANAGER_WRITE_STATUSES = {
    Decision.Status.DRAFT,
    Decision.Status.FRAMING,
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
}
CONTRIBUTOR_ROLES = {
    Participant.Role.DECISION_MAKER,
    Participant.Role.CONTRIBUTOR,
    Participant.Role.REVIEWER,
}
REVIEW_ROLES = {
    Participant.Role.DECISION_MAKER,
    Participant.Role.REVIEWER,
}


def _participant_role(*, actor: User, decision: Decision) -> str | None:
    return (
        decision.participants.filter(
            user=actor,
            status=Participant.Status.ACTIVE,
        )
        .values_list("role", flat=True)
        .first()
    )


def can_contribute_reasoning(*, actor: User, decision: Decision) -> bool:
    """Return whether the actor may create a structured reasoning record."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    if membership.role in MANAGER_ROLES or decision.owner_id == actor.id:
        return decision.status in MANAGER_WRITE_STATUSES
    participant_role = _participant_role(actor=actor, decision=decision)
    if decision.status == Decision.Status.OPEN_FOR_CONTRIBUTION:
        return participant_role in CONTRIBUTOR_ROLES
    if decision.status == Decision.Status.UNDER_REVIEW:
        return participant_role in REVIEW_ROLES
    return False


def can_edit_reasoning(
    *,
    actor: User,
    decision: Decision,
    created_by_id: object,
    accountable_user_id: object | None = None,
) -> bool:
    """Return whether the actor may edit or change the state of one record."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    if membership.role in MANAGER_ROLES or decision.owner_id == actor.id:
        return decision.status in MANAGER_WRITE_STATUSES
    if created_by_id != actor.id and accountable_user_id != actor.id:
        return False
    participant_role = _participant_role(actor=actor, decision=decision)
    if decision.status == Decision.Status.OPEN_FOR_CONTRIBUTION:
        return participant_role in CONTRIBUTOR_ROLES
    if decision.status == Decision.Status.UNDER_REVIEW:
        return participant_role in REVIEW_ROLES
    return False


def require_active_membership(*, actor: User, decision: Decision) -> Membership:
    """Return active tenant membership or fail at the service boundary."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied("You are not an active member of this organisation.")
    return membership
