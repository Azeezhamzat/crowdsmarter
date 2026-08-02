"""Named capabilities for integrated decision analysis."""

from apps.decisions.models import Decision
from apps.decisions.policies import MANAGER_ROLES, active_membership
from apps.organisations.models import Membership
from apps.participants.models import Participant


WRITABLE_STATUSES = {
    Decision.Status.DRAFT,
    Decision.Status.FRAMING,
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
    Decision.Status.READY_FOR_DECISION,
}


def can_manage_analysis(*, actor, decision: Decision) -> bool:
    membership = active_membership(actor=actor, decision=decision)
    if membership is None or decision.status not in WRITABLE_STATUSES:
        return False
    if membership.role in MANAGER_ROLES or decision.owner_id == actor.id:
        return True
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
        role=Participant.Role.DECISION_MAKER,
    ).exists()


def can_contribute_analysis(*, actor, decision: Decision) -> bool:
    membership = active_membership(actor=actor, decision=decision)
    if membership is None or decision.status not in WRITABLE_STATUSES:
        return False
    if can_manage_analysis(actor=actor, decision=decision):
        return True
    if membership.role == Membership.Role.VIEWER:
        return False
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
    ).exclude(role=Participant.Role.OBSERVER).exists()


def can_edit_issue(*, actor, issue) -> bool:
    """Allow accountable managers or the assigned owner to update an issue."""
    if not can_contribute_analysis(actor=actor, decision=issue.decision):
        return False
    return can_manage_analysis(actor=actor, decision=issue.decision) or issue.owner_id == actor.id
