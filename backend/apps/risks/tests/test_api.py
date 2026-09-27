import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_risk_api_create_list_and_change_status(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("risks:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        collection,
        {
            "title": "False-positive alerts",
            "description": "Too many false alerts may reduce staff trust in the system.",
            "likelihood": 3,
            "impact": 4,
            "response_strategy": "mitigate",
            "mitigation_plan": "Define thresholds and review alerts weekly during the pilot.",
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["score"] == 12
    assert len(api_client.get(collection).json()) == 1
    detail = reverse("risks:detail", kwargs={"risk_id": response.json()["id"]})
    patch = api_client.patch(detail, {"status": "monitoring"}, format="json")
    assert patch.status_code == 200
    assert patch.json()["status"] == "monitoring"


@pytest.mark.django_db
def test_risk_api_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(user_factory())
    assert (
        api_client.get(
            reverse("risks:list-create", kwargs={"decision_id": decision.id})
        ).status_code
        == 404
    )
