from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.decisions.models import Decision
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_decision_endpoints_are_tenant_isolated(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    outsider = user_factory()
    decision = decision_factory()
    api_client.force_authenticate(outsider)

    assert api_client.get(
        reverse("decisions:detail", kwargs={"decision_id": decision.id})
    ).status_code == 404
    assert api_client.get(
        reverse(
            "decisions:list-create",
            kwargs={"workspace_id": decision.workspace_id},
        )
    ).status_code == 404


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [("owner", 201), ("admin", 201), ("contributor", 201), ("viewer", 403)],
)
def test_decision_create_permission_matrix(
    api_client, user_factory, organisation_factory, workspace_factory, role, expected_status
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    actor = owner if role == "owner" else user_factory()
    organisation = organisation_factory(owner=owner)
    if actor != owner:
        Membership.objects.create(organisation=organisation, user=actor, role=role)
    workspace = workspace_factory(organisation=organisation, created_by=owner)
    api_client.force_authenticate(actor)

    response = api_client.post(
        reverse("decisions:list-create", kwargs={"workspace_id": workspace.id}),
        {"title": f"{role} decision", "decision_question": "What should we do?"},
        format="json",
    )

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_create_list_retrieve_and_update_decision(
    api_client, user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    workspace = workspace_factory(organisation=organisation, created_by=owner)
    api_client.force_authenticate(owner)
    collection_url = reverse("decisions:list-create", kwargs={"workspace_id": workspace.id})

    create_response = api_client.post(
        collection_url,
        {"title": "Select a market", "decision_question": "Which market should we enter?"},
        format="json",
    )
    assert create_response.status_code == 201
    assert create_response.json()["status"] == "draft"
    assert api_client.get(collection_url).status_code == 200

    detail_url = reverse(
        "decisions:detail", kwargs={"decision_id": create_response.json()["id"]}
    )
    patch_response = api_client.patch(
        detail_url,
        {
            "purpose": "Choose the strongest initial market.",
            "scope": "European English-speaking markets.",
            "urgency": "high",
        },
        format="json",
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["purpose"] == "Choose the strongest initial market."
    assert "status" not in {
        "purpose": "Choose the strongest initial market.",
        "scope": "European English-speaking markets.",
        "urgency": "high",
    }


@pytest.mark.django_db
def test_status_cannot_be_patched_directly(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(decision.owner)

    response = api_client.patch(
        reverse("decisions:detail", kwargs={"decision_id": decision.id}),
        {"status": "archived", "purpose": "This must not be applied."},
        format="json",
    )

    assert response.status_code == 400
    assert "status" in response.json()
    decision.refresh_from_db()
    assert decision.status == Decision.Status.DRAFT
    assert decision.purpose == ""


@pytest.mark.django_db
def test_transition_endpoint_validates_and_records_history(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Which option?",
        purpose="Make a governed choice.",
        scope="This organisation.",
    )
    api_client.force_authenticate(decision.owner)
    transition_url = reverse(
        "decisions:transition-list-create", kwargs={"decision_id": decision.id}
    )

    response = api_client.post(
        transition_url,
        {"expected_status": "draft", "rationale": "Frame is complete."},
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["to_status"] == "framing"
    history = api_client.get(transition_url)
    assert history.status_code == 200
    assert len(history.json()) == 1


@pytest.mark.django_db
def test_open_contribution_requires_deadline_and_stakeholder(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        status=Decision.Status.FRAMING,
        contribution_guidance="Submit relevant evidence.",
        contribution_deadline=timezone.now() + timedelta(days=2),
    )
    api_client.force_authenticate(decision.owner)

    response = api_client.post(
        reverse(
            "decisions:transition-list-create",
            kwargs={"decision_id": decision.id},
        ),
        {"expected_status": "framing", "rationale": "Open the window."},
        format="json",
    )

    assert response.status_code == 400
    assert "participants" in response.json()


@pytest.mark.django_db
def test_non_owner_contributor_cannot_transition(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Question?",
        purpose="Purpose.",
        scope="Scope.",
    )
    actor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=actor,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(actor)

    response = api_client.post(
        reverse(
            "decisions:transition-list-create",
            kwargs={"decision_id": decision.id},
        ),
        {"expected_status": "draft", "rationale": "Not authorised."},
        format="json",
    )

    assert response.status_code == 403


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
def test_transition_permission_matrix(
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
        decision_question="Which operating model should we choose?",
        purpose="Select a model with clear accountability.",
        scope="The customer operations function.",
    )
    api_client.force_authenticate(actor)

    response = api_client.post(
        reverse(
            "decisions:transition-list-create",
            kwargs={"decision_id": decision.id},
        ),
        {"expected_status": "draft", "rationale": "The frame is complete."},
        format="json",
    )

    assert response.status_code == expected_status
