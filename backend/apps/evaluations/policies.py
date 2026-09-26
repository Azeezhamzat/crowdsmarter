"""Named capabilities for evaluation and prioritisation."""

from apps.organisations.models import Membership
from apps.participants.models import Participant


def active_membership(*, actor, organisation):
    return organisation.memberships.filter(user=actor, status=Membership.Status.ACTIVE).first()


def can_manage_exercise(*, actor, exercise):
    membership = active_membership(actor=actor, organisation=exercise.organisation)
    if membership is None:
        return False
    if (
        membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}
        or exercise.owner_id == actor.id
        or exercise.decision.owner_id == actor.id
    ):
        return True
    return exercise.decision.participants.filter(
        user=actor, status=Participant.Status.ACTIVE, role=Participant.Role.DECISION_MAKER
    ).exists()


def can_submit_evaluation(*, actor, exercise):
    membership = active_membership(actor=actor, organisation=exercise.organisation)
    if membership is None:
        return False
    return (
        exercise.decision.participants.filter(user=actor, status=Participant.Status.ACTIVE)
        .exclude(role=Participant.Role.OBSERVER)
        .exists()
    )


def can_manage_portfolio(*, actor, portfolio):
    membership = active_membership(actor=actor, organisation=portfolio.organisation)
    return membership is not None and (
        membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}
        or portfolio.owner_id == actor.id
    )


def can_assess_portfolio(*, actor, portfolio):
    membership = active_membership(actor=actor, organisation=portfolio.organisation)
    return membership is not None and membership.role != Membership.Role.VIEWER
