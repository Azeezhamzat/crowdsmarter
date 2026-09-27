import pytest
from django.urls import reverse

from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_participant_endpoints_are_tenant_isolated(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    participant = Participant.objects.get(
        decision=decision,
        role=Participant.Role.DECISION_OWNER,
    )
    outsider = user_factory()
    api_client.force_authenticate(outsider)

    assert (
        api_client.get(
            reverse(
                "participants:list-create",
                kwargs={"decision_id": decision.id},
            )
        ).status_code
        == 404
    )
    assert (
        api_client.patch(
            reverse(
                "participants:detail",
                kwargs={"participant_id": participant.id},
            ),
            {"role": "reviewer"},
            format="json",
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_add_list_change_and_remove_participant(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    stakeholder = user_factory(email="stakeholder@example.com")
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(decision.owner)
    collection_url = reverse("participants:list-create", kwargs={"decision_id": decision.id})

    create_response = api_client.post(
        collection_url,
        {"email": stakeholder.email, "role": "contributor"},
        format="json",
    )
    assert create_response.status_code == 201
    assert len(api_client.get(collection_url).json()) == 2

    detail_url = reverse(
        "participants:detail",
        kwargs={"participant_id": create_response.json()["id"]},
    )
    patch_response = api_client.patch(detail_url, {"role": "reviewer"}, format="json")
    assert patch_response.status_code == 200
    assert patch_response.json()["role"] == "reviewer"
    assert api_client.delete(detail_url).status_code == 204
    assert len(api_client.get(collection_url).json()) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "owns_decision", "expected_status"),
    [
        ("owner", False, 201),
        ("admin", False, 201),
        ("contributor", True, 201),
        ("contributor", False, 403),
        ("viewer", False, 403),
    ],
)
def test_participant_create_permission_matrix(
    api_client,
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
    role,
    owns_decision,
    expected_status,
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
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(actor)

    response = api_client.post(
        reverse(
            "participants:list-create",
            kwargs={"decision_id": decision.id},
        ),
        {"email": stakeholder.email, "role": "observer"},
        format="json",
    )

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_under_review_decision_rejects_participant_changes(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(decision.owner)

    response = api_client.post(
        reverse(
            "participants:list-create",
            kwargs={"decision_id": decision.id},
        ),
        {"email": stakeholder.email, "role": "reviewer"},
        format="json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_reviewer_declares_and_withdraws_conflict_via_api(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import create_option

    decision = decision_factory()
    option = create_option(
        actor=decision.owner, decision=decision, title="App", description="Desc."
    )
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=reviewer,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    participant = Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
        added_by=decision.owner,
    )
    api_client.force_authenticate(reviewer)

    create_response = api_client.post(
        reverse("participants:conflict-list-create", kwargs={"participant_id": participant.id}),
        {"scope": "option", "option_id": str(option.id), "reason": "I sit on their board."},
        format="json",
    )
    assert create_response.status_code == 201
    conflict_id = create_response.json()["id"]

    list_response = api_client.get(
        reverse("participants:conflict-list-create", kwargs={"participant_id": participant.id})
    )
    assert len(list_response.json()) == 1

    withdraw_response = api_client.post(
        reverse("participants:conflict-withdraw", kwargs={"conflict_id": conflict_id})
    )
    assert withdraw_response.status_code == 200
    assert withdraw_response.json()["withdrawn_at"] is not None
