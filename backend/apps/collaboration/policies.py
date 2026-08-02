"""Collaboration authorisation policies."""

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant

from .models import DiscussionEntry


def active_membership(*, actor: User, decision: Decision) -> Membership | None:
    return decision.organisation.memberships.filter(
        user=actor,
        status=Membership.Status.ACTIVE,
    ).first()


def can_contribute(*, actor: User, decision: Decision) -> bool:
    """Allow active managers or non-observer decision participants to contribute."""
    if decision.status == Decision.Status.ARCHIVED:
        return False
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    if membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        return True
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
    ).exclude(role=Participant.Role.OBSERVER).exists()


def can_resolve(*, actor: User, entry: DiscussionEntry) -> bool:
    """Allow the decision owner or tenant managers to resolve open items."""
    membership = active_membership(actor=actor, decision=entry.decision)
    if membership is None or entry.decision.status == Decision.Status.ARCHIVED:
        return False
    if membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        return True
    return entry.decision.owner_id == actor.id
