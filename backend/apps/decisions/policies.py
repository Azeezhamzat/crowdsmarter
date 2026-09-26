"""Named decision capabilities combining tenant role and lifecycle state."""

from __future__ import annotations

from apps.accounts.models import User
from apps.organisations.models import Membership
from apps.participants.models import Participant

from .models import Decision

MANAGER_ROLES = {Membership.Role.OWNER, Membership.Role.ADMIN}
CREATOR_ROLES = MANAGER_ROLES | {Membership.Role.CONTRIBUTOR}
EDITABLE_STATUSES = {Decision.Status.DRAFT, Decision.Status.FRAMING}


def active_membership(*, actor: User, decision: Decision) -> Membership | None:
    """Return the actor's active membership for the decision tenant."""
    return decision.organisation.memberships.filter(
        user=actor,
        status=Membership.Status.ACTIVE,
    ).first()


def can_create_decision(*, membership: Membership | None) -> bool:
    """Return whether a membership may initiate a decision."""
    return membership is not None and membership.role in CREATOR_ROLES


def can_edit_decision(*, actor: User, decision: Decision) -> bool:
    """Return whether framing fields may be changed in the current state."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None or decision.status not in EDITABLE_STATUSES:
        return False
    return membership.role in MANAGER_ROLES or decision.owner_id == actor.id


def can_transition_decision(*, actor: User, decision: Decision) -> bool:
    """Return whether the actor holds human lifecycle authority."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    return membership.role in MANAGER_ROLES or decision.owner_id == actor.id


def can_manage_participants(*, actor: User, decision: Decision) -> bool:
    """Return whether the actor may curate decision participation."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None or decision.status not in {
        Decision.Status.DRAFT,
        Decision.Status.FRAMING,
        Decision.Status.OPEN_FOR_CONTRIBUTION,
    }:
        return False
    return membership.role in MANAGER_ROLES or decision.owner_id == actor.id


def has_finalisation_authority(*, actor: User, decision: Decision) -> bool:
    """Return whether the actor holds human authority to author finalisation."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    if membership.role in MANAGER_ROLES or decision.owner_id == actor.id:
        return True
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
        role=Participant.Role.DECISION_MAKER,
    ).exists()


def can_finalise_decision(*, actor: User, decision: Decision) -> bool:
    """Return whether authority and lifecycle state permit finalisation now."""
    return decision.status == Decision.Status.READY_FOR_DECISION and has_finalisation_authority(
        actor=actor, decision=decision
    )
