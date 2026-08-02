"""Human-authority policies for AI assistance."""

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.organisations.models import Membership

from .models import AIReview


_REQUESTABLE_STATUSES = {
    Decision.Status.FRAMING,
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
    Decision.Status.READY_FOR_DECISION,
    Decision.Status.DECISION_FINALISED,
    Decision.Status.COMMITMENT,
    Decision.Status.IMPLEMENTATION,
    Decision.Status.OUTCOME_REVIEW,
    Decision.Status.LESSONS_LEARNED,
}


def membership_for(*, user: User, decision: Decision) -> Membership | None:
    return Membership.objects.filter(
        organisation=decision.organisation,
        user=user,
        status=Membership.Status.ACTIVE,
    ).first()


def can_request_ai_review(*, actor: User, decision: Decision) -> bool:
    membership = membership_for(user=actor, decision=decision)
    return bool(
        membership
        and membership.role
        in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
            Membership.Role.CONTRIBUTOR,
        }
        and decision.status in _REQUESTABLE_STATUSES
    )


def can_moderate_ai_review(*, actor: User, review: AIReview) -> bool:
    if actor.id in {review.requested_by_id, review.decision.owner_id}:
        return True
    membership = membership_for(user=actor, decision=review.decision)
    return bool(
        membership
        and membership.role in {Membership.Role.OWNER, Membership.Role.ADMIN}
    )
