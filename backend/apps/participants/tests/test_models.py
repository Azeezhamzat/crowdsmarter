import pytest
from django.core.exceptions import ValidationError

from apps.participants.models import Participant


@pytest.mark.django_db
def test_removed_participant_requires_removal_metadata(
    decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    user = user_factory()
    participant = Participant(
        organisation=decision.organisation,
        decision=decision,
        user=user,
        role=Participant.Role.CONTRIBUTOR,
        status=Participant.Status.REMOVED,
        added_by=decision.owner,
    )

    with pytest.raises(ValidationError, match="removal timestamp"):
        participant.full_clean(validate_unique=False, validate_constraints=False)
