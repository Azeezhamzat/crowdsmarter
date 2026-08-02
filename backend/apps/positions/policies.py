"""Capabilities for stakeholder position submission."""

from __future__ import annotations

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant


POSITION_STATUSES = {
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
    Decision.Status.READY_FOR_DECISION,
}
SUBMITTER_ROLES = {
    Participant.Role.DECISION_OWNER,
    Participant.Role.DECISION_MAKER,
    Participant.Role.CONTRIBUTOR,
    Participant.Role.REVIEWER,
}


def active_position_participant(*, actor: User, decision: Decision) -> Participant | None:
    """Return an eligible active participant for the actor."""
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
        role__in=SUBMITTER_ROLES,
    ).first()


def can_submit_position(*, actor: User, decision: Decision) -> bool:
    """Return whether the actor may submit their own current recommendation."""
    if decision.status not in POSITION_STATUSES:
        return False
    if not decision.organisation.memberships.filter(
        user=actor,
        status=Membership.Status.ACTIVE,
    ).exists():
        return False
    return active_position_participant(actor=actor, decision=decision) is not None
