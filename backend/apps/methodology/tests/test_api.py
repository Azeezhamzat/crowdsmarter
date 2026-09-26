import pytest
from django.urls import reverse

from apps.methodology.models import DecisionMethod
from apps.organisations.models import Membership

METHOD_PAYLOAD = {
    "name": "Strategic investment method",
    "summary": "A governed method for material investment choices.",
    "best_for": "Cross-functional investment decisions.",
    "question_prompt": "State the investment choice as a decision question.",
    "purpose_prompt": "Explain the customer and organisational value.",
    "context_prompt": "Describe the evidence and strategic context.",
    "scope_prompt": "State what is inside and outside this decision.",
    "contribution_prompt": "Explain what contributors should provide.",
    "suggested_urgency": "normal",
    "required_fields": ["decision_question", "purpose", "context", "scope"],
    "checklist": ["The status quo is explicit."],
    "evidence_prompts": ["What evidence challenges the leading option?"],
    "assumption_prompts": [],
    "risk_prompts": [],
    "stakeholder_prompts": [],
    "lifecycle_expectations": ["Review the decision after implementation."],
}


@pytest.mark.django_db
def test_draft_methods_are_governed_and_hidden_from_ordinary_members(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="method-owner@example.com")
    contributor = user_factory(email="method-contributor@example.com")
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    url = reverse("methodology:method-list-create", kwargs={"organisation_id": organisation.id})

    api_client.force_authenticate(owner)
    invalid = api_client.post(
        url, {**METHOD_PAYLOAD, "preferred_option": "Option A"}, format="json"
    )
    assert invalid.status_code == 400
    assert "preferred_option" in invalid.json()

    created = api_client.post(url, METHOD_PAYLOAD, format="json")
    assert created.status_code == 201
    version_id = created.json()["versions"][0]["id"]

    api_client.force_authenticate(contributor)
    assert api_client.get(url).json() == []
    assert (
        api_client.get(
            reverse("methodology:version-detail", kwargs={"version_id": version_id})
        ).status_code
        == 404
    )

    api_client.force_authenticate(owner)
    approved = api_client.post(
        reverse("methodology:version-approve", kwargs={"version_id": version_id}), {}, format="json"
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    api_client.force_authenticate(contributor)
    visible = api_client.get(url)
    assert visible.status_code == 200
    assert visible.json()[0]["status"] == "approved"


@pytest.mark.django_db
def test_only_owner_can_approve_and_approved_versions_are_immutable(
    api_client, organisation_factory, user_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory(email="owner-approve@example.com")
    admin = user_factory(email="admin-method@example.com")
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=admin,
        role=Membership.Role.ADMIN,
        status=Membership.Status.ACTIVE,
    )
    list_url = reverse(
        "methodology:method-list-create", kwargs={"organisation_id": organisation.id}
    )
    api_client.force_authenticate(owner)
    created = api_client.post(list_url, METHOD_PAYLOAD, format="json")
    version_id = created.json()["versions"][0]["id"]

    api_client.force_authenticate(admin)
    denied = api_client.post(
        reverse("methodology:version-approve", kwargs={"version_id": version_id}), {}, format="json"
    )
    assert denied.status_code == 403

    api_client.force_authenticate(owner)
    assert (
        api_client.post(
            reverse("methodology:version-approve", kwargs={"version_id": version_id}),
            {},
            format="json",
        ).status_code
        == 200
    )
    immutable = api_client.patch(
        reverse("methodology:version-detail", kwargs={"version_id": version_id}),
        {"question_prompt": "Silently replace the approved method."},
        format="json",
    )
    assert immutable.status_code == 400
    assert (
        DecisionMethod.objects.get(organisation=organisation).status
        == DecisionMethod.Status.APPROVED
    )


@pytest.mark.django_db
def test_method_records_are_tenant_isolated(api_client, organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    owner = user_factory(email="visible-method-owner@example.com")
    outsider = user_factory(email="method-outsider@example.com")
    organisation = organisation_factory(owner=owner)
    api_client.force_authenticate(owner)
    created = api_client.post(
        reverse("methodology:method-list-create", kwargs={"organisation_id": organisation.id}),
        METHOD_PAYLOAD,
        format="json",
    )
    method_id = created.json()["id"]

    api_client.force_authenticate(outsider)
    assert (
        api_client.get(
            reverse("methodology:method-detail", kwargs={"method_id": method_id})
        ).status_code
        == 404
    )
