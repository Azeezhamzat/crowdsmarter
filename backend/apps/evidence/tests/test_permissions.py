import pytest

from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_reviewer_can_contribute_during_review(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=reviewer,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
        added_by=decision.owner,
    )

    assert can_contribute_reasoning(actor=reviewer, decision=decision)
