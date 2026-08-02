import pytest

from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_observer_cannot_add_assumption(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    observer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=observer,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=decision.owner,
    )

    assert not can_contribute_reasoning(actor=observer, decision=decision)


@pytest.mark.django_db
def test_accountable_reviewer_can_edit_owned_reasoning_record(
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

    assert can_edit_reasoning(
        actor=reviewer,
        decision=decision,
        created_by_id=decision.owner_id,
        accountable_user_id=reviewer.id,
    )
