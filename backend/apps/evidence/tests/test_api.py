import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_evidence_api_create_list_and_patch(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    url = reverse("evidence:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        url,
        {
            "title": "Field trial report",
            "summary": "The field trial found acceptable detection performance.",
            "source_type": "research",
            "source_reference": "Field trial report 2026",
            "source_url": "",
            "stance": "supports",
            "strength": "moderate",
        },
        format="json",
    )

    assert response.status_code == 201
    assert len(api_client.get(url).json()) == 1
    detail = reverse("evidence:detail", kwargs={"evidence_id": response.json()["id"]})
    assert api_client.patch(detail, {"strength": "high"}, format="json").status_code == 200


@pytest.mark.django_db
def test_evidence_api_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(user_factory())
    response = api_client.get(reverse("evidence:list-create", kwargs={"decision_id": decision.id}))
    assert response.status_code == 404
