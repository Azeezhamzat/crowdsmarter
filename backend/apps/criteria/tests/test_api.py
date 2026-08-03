import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_criterion_api_create_list_and_update(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("criteria:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        collection,
        {
            "title": "Implementation risk",
            "description": "How likely the option is to fail during rollout.",
            "direction": "minimize",
            "weight": 35,
            "is_must_have": False,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["weight"] == 35
    assert len(api_client.get(collection).json()) == 1
    detail = reverse("criteria:detail", kwargs={"criterion_id": response.json()["id"]})
    patch = api_client.patch(detail, {"weight": 50}, format="json")
    assert patch.status_code == 200
    assert patch.json()["weight"] == 50


@pytest.mark.django_db
def test_must_have_criterion_requires_threshold_via_api(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("criteria:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        collection,
        {
            "title": "Budget ceiling",
            "description": "The option must fit within the approved budget.",
            "direction": "minimize",
            "weight": 50,
            "is_must_have": True,
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_criterion_api_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(user_factory())
    assert api_client.get(
        reverse("criteria:list-create", kwargs={"decision_id": decision.id})
    ).status_code == 404
