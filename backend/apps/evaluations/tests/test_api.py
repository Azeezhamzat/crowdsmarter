import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_evaluation_api_is_strict_and_tenant_safe(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id}),
        {
            "title": "Blind scorecard",
            "purpose": "Compare alternatives independently.",
            "method": "scorecard",
            "anonymity": "peer_anonymous",
            "blind_results_until_close": True,
            "quorum_count": 1,
            "approval_threshold": 60,
            "objection_threshold": 20,
            "owner_id": str(owner.id),
            "manufactured_consensus": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "manufactured_consensus" in response.json()

    api_client.force_authenticate(user_factory())
    hidden = api_client.get(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id})
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_prioritisation_api_creates_portfolio(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("evaluations:prioritisation-portfolios", kwargs={"organisation_id": organisation.id}),
        {
            "title": "Annual investment portfolio",
            "purpose": "Choose initiatives within the delivery envelope.",
            "budget_limit": "100000.00",
            "capacity_limit": "12.00",
            "owner_id": str(owner.id),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["recommendation"]["warning"].startswith("This is an explainable")
