import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_option_endpoint_create_list_and_withdraw(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.FRAMING)
    api_client.force_authenticate(decision.owner)
    collection = reverse("decision_options:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        collection,
        {
            "title": "Run a pilot",
            "description": "Test the approach before wider adoption.",
            "expected_benefits": "Local evidence with limited exposure.",
            "tradeoffs": "The pilot delays full rollout.",
            "is_status_quo": False,
        },
        format="json",
    )

    assert response.status_code == 201
    assert api_client.get(collection).status_code == 200
    detail = reverse("decision_options:detail", kwargs={"option_id": response.json()["id"]})
    patch = api_client.patch(detail, {"status": "withdrawn"}, format="json")
    assert patch.status_code == 200
    assert patch.json()["status"] == "withdrawn"


@pytest.mark.django_db
def test_option_endpoint_rejects_unknown_field(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.FRAMING)
    api_client.force_authenticate(decision.owner)

    response = api_client.post(
        reverse("decision_options:list-create", kwargs={"decision_id": decision.id}),
        {
            "title": "Valid title",
            "description": "A sufficiently detailed option description.",
            "selected_by_ai": True,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "selected_by_ai" in response.json()


@pytest.mark.django_db
def test_option_endpoint_creates_dependency_between_two_options(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.FRAMING)
    api_client.force_authenticate(decision.owner)
    collection = reverse("decision_options:list-create", kwargs={"decision_id": decision.id})

    prerequisite = api_client.post(
        collection,
        {"title": "Data migration", "description": "Migrate legacy records first."},
        format="json",
    ).json()
    dependent = api_client.post(
        collection,
        {
            "title": "New reporting suite",
            "description": "Requires migrated data to function.",
            "estimated_cost": "12000.00",
            "reversibility": "partially_reversible",
            "depends_on_ids": [prerequisite["id"]],
        },
        format="json",
    )

    assert dependent.status_code == 201
    assert dependent.json()["depends_on_ids"] == [prerequisite["id"]]
    assert dependent.json()["estimated_cost"] == "12000.00"


@pytest.mark.django_db
def test_option_endpoint_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.FRAMING)
    outsider = user_factory()
    api_client.force_authenticate(outsider)

    response = api_client.get(
        reverse("decision_options:list-create", kwargs={"decision_id": decision.id})
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_eligibility_and_outcome_endpoints(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("decision_options:list-create", kwargs={"decision_id": decision.id})
    option_id = api_client.post(
        collection,
        {
            "title": "Grant application",
            "description": "Reduces post-harvest loss.",
            "estimated_cost": "3000.00",
        },
        format="json",
    ).json()["id"]

    eligibility = api_client.post(
        reverse("decision_options:eligibility", kwargs={"option_id": option_id}),
        {"eligibility_status": "eligible", "eligibility_note": "Meets criteria."},
        format="json",
    )
    assert eligibility.status_code == 200
    assert eligibility.json()["eligibility_status"] == "eligible"

    outcome = api_client.post(
        reverse("decision_options:outcome", kwargs={"option_id": option_id}),
        {"outcome_status": "funded", "awarded_amount": "2500.00"},
        format="json",
    )
    assert outcome.status_code == 200
    assert outcome.json()["outcome_status"] == "funded"
    assert outcome.json()["awarded_amount"] == "2500.00"


@pytest.mark.django_db
def test_funded_outcome_without_amount_is_rejected(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("decision_options:list-create", kwargs={"decision_id": decision.id})
    option_id = api_client.post(
        collection,
        {"title": "App", "description": "Desc."},
        format="json",
    ).json()["id"]

    response = api_client.post(
        reverse("decision_options:outcome", kwargs={"option_id": option_id}),
        {"outcome_status": "funded"},
        format="json",
    )

    assert response.status_code == 400
    assert "awarded_amount" in response.json()
