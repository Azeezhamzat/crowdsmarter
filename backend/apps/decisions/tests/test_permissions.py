import pytest
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.decisions.models import Decision
from apps.decisions.permissions import CanAccessDecision
from apps.decisions.policies import can_finalise_decision
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "owns_decision", "can_patch"),
    [
        ("owner", False, True),
        ("admin", False, True),
        ("contributor", True, True),
        ("contributor", False, False),
        ("viewer", False, False),
    ],
)
def test_decision_object_permission_matrix(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
    role,
    owns_decision,
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
        owner=actor if owns_decision else organisation_owner,
        created_by=organisation_owner,
    )
    request = APIRequestFactory().patch("/", {})
    force_authenticate(request, actor)

    assert (
        CanAccessDecision().has_object_permission(request, object(), decision)
        is can_patch
    )


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("membership_role", "participant_role", "expected"),
    [
        (Membership.Role.ADMIN, None, True),
        (Membership.Role.CONTRIBUTOR, Participant.Role.DECISION_MAKER, True),
        (Membership.Role.CONTRIBUTOR, Participant.Role.CONTRIBUTOR, False),
        (Membership.Role.VIEWER, None, False),
    ],
)
def test_finalisation_permission_matrix(
    user_factory,
    decision_factory,
    membership_role,
    participant_role,
    expected,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    actor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=actor,
        role=membership_role,
    )
    if participant_role:
        Participant.objects.create(
            organisation=decision.organisation,
            decision=decision,
            user=actor,
            role=participant_role,
            added_by=decision.owner,
        )

    assert can_finalise_decision(actor=actor, decision=decision) is expected
