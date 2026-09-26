"""Named contribution-orchestration capabilities."""

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


def has_contribution_authority(*, actor, decision: Decision) -> bool:
    """Return accountable authority independently of whether the decision is writable."""
    membership = active_membership(actor=actor, decision=decision)
    if membership is None:
        return False
    if membership.role in MANAGER_ROLES or decision.owner_id == actor.id:
        return True
    return decision.participants.filter(
        user=actor,
        status=Participant.Status.ACTIVE,
        role__in=[Participant.Role.DECISION_MAKER, Participant.Role.REVIEWER],
    ).exists()


def can_manage_contributions(*, actor, decision: Decision) -> bool:
    return decision.status in WRITABLE_STATUSES and has_contribution_authority(
        actor=actor, decision=decision
    )


def can_receive_assignment(*, actor, decision: Decision) -> bool:
    membership = active_membership(actor=actor, decision=decision)
    if membership is None or membership.role == Membership.Role.VIEWER:
        return False
    return (
        decision.participants.filter(user=actor, status=Participant.Status.ACTIVE)
        .exclude(role=Participant.Role.OBSERVER)
        .exists()
    )


def can_view_request(*, actor, request) -> bool:
    membership = active_membership(actor=actor, decision=request.decision)
    if membership is None:
        return False
    if request.status == request.Status.DRAFT:
        return has_contribution_authority(actor=actor, decision=request.decision)
    if can_manage_contributions(actor=actor, decision=request.decision):
        return True
    return request.decision.participants.filter(
        user=actor, status=Participant.Status.ACTIVE
    ).exists()


def can_work_on_request(*, actor, request) -> bool:
    return (
        request.decision.status in WRITABLE_STATUSES
        and request.assignee_id == actor.id
        and can_receive_assignment(actor=actor, decision=request.decision)
        and request.status
        in {
            request.Status.OPEN,
            request.Status.IN_PROGRESS,
            request.Status.RETURNED,
        }
    )


def can_review_request(*, actor, request) -> bool:
    if request.decision.status not in WRITABLE_STATUSES:
        return False
    if request.reviewer_id == actor.id:
        return can_receive_assignment(actor=actor, decision=request.decision)
    return can_manage_contributions(actor=actor, decision=request.decision)
