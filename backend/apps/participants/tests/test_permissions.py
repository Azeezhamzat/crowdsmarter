import pytest
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.participants.permissions import CanAccessParticipant


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "is_decision_owner", "can_patch"),
    [
        ("owner", False, True),
        ("admin", False, True),
        ("contributor", True, True),
        ("contributor", False, False),
        ("viewer", False, False),
    ],
)
def test_participant_object_permission_matrix(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
    role,
    is_decision_owner,
    can_patch,
):  # type: ignore[no-untyped-def]
    organisation_owner = user_factory()
    organisation = organisation_factory(owner=organisation_owner)
    workspace = workspace_factory(
        organisation=organisation,
        created_by=organisation_owner,
    )

    if role == "owner":
        actor = organisation_owner
    else:
        actor = user_factory()
        Membership.objects.create(
            organisation=organisation,
            user=actor,
            role=role,
        )

    decision = decision_factory(
        workspace=workspace,
        owner=actor if is_decision_owner else organisation_owner,
        created_by=organisation_owner,
    )
    participant = Participant.objects.get(
        decision=decision,
        role=Participant.Role.DECISION_OWNER,
    )
    request = APIRequestFactory().patch("/", {})
    force_authenticate(request, actor)
    request = Request(request)

    assert (
        CanAccessParticipant().has_object_permission(request, object(), participant)
        is can_patch
    )
