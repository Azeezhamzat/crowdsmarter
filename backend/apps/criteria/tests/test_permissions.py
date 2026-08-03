import pytest

from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_contributor_cannot_add_criterion_during_review(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )

    assert not can_contribute_reasoning(actor=contributor, decision=decision)
