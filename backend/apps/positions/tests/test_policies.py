import pytest

from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.participants.services import add_participant
from apps.positions.policies import can_submit_position


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
def test_position_submission_permission_matrix(
    user_factory,
    decision_factory,
    participant_role,
    expected,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    actor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=actor,
        role=Membership.Role.CONTRIBUTOR,
    )
    add_participant(
        actor=decision.owner,
        decision=decision,
        user=actor,
        role=participant_role,
    )

    assert can_submit_position(actor=actor, decision=decision) is expected
