import pytest

from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("participant_role", "expected"),
    [
        (Participant.Role.DECISION_MAKER, True),
        (Participant.Role.CONTRIBUTOR, True),
        (Participant.Role.REVIEWER, True),
        (Participant.Role.OBSERVER, False),
    ],
)
def test_open_contribution_permission_matrix(
    user_factory, decision_factory, participant_role, expected
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    actor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=actor,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=actor,
        role=participant_role,
        added_by=decision.owner,
    )

    assert can_contribute_reasoning(actor=actor, decision=decision) is expected


@pytest.mark.django_db
def test_contributor_cannot_edit_another_authors_option(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    actor = user_factory()
    author = user_factory()
    for user in (actor, author):
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
        )
        Participant.objects.create(
            organisation=decision.organisation,
            decision=decision,
            user=user,
            role=Participant.Role.CONTRIBUTOR,
            added_by=decision.owner,
        )
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        title="Author-owned option",
        description="Only its creator or a decision authority may edit it.",
        proposed_by=author,
        created_by=author,
    )

    assert not can_edit_reasoning(
        actor=actor,
        decision=decision,
        created_by_id=option.created_by_id,
    )
