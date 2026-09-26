import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_lessons_api_create_list_retire_and_archive(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    api_client.force_authenticate(decision.owner)
    list_url = reverse("lessons:list-create", kwargs={"decision_id": decision.id})
    response = api_client.post(
        list_url,
        {
            "title": "Validate training needs",
            "insight": "Implementation readiness was weaker than expected.",
            "category": "implementation",
            "applicability": "Future technology pilots.",
            "recommended_change": "Add a readiness review.",
        },
        format="json",
    )
    assert response.status_code == 201
    lesson_id = response.json()["id"]
    assert len(api_client.get(list_url).json()) == 1
    detail_url = reverse("lessons:detail", kwargs={"lesson_id": lesson_id})
    update_response = api_client.patch(
        detail_url,
        {"recommended_change": "Require a readiness review and training plan."},
        format="json",
    )
    assert update_response.status_code == 200

    retire_response = api_client.delete(detail_url)
    assert retire_response.status_code == 200
    assert retire_response.json()["status"] == "retired"

    replacement = api_client.post(
        list_url,
        {
            "title": "Keep a baseline",
            "insight": "Without a baseline the outcome was harder to interpret.",
            "category": "evidence",
            "applicability": "All future pilots.",
            "recommended_change": "Require baseline evidence during framing.",
        },
        format="json",
    )
    assert replacement.status_code == 201
    archive_response = api_client.post(
        reverse("lessons:archive", kwargs={"decision_id": decision.id}),
        {
            "expected_status": "lessons_learned",
            "rationale": "The learning record is complete.",
        },
        format="json",
    )
    assert archive_response.status_code == 204


@pytest.mark.django_db
def test_lessons_api_is_tenant_isolated(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    api_client.force_authenticate(user_factory())
    response = api_client.get(reverse("lessons:list-create", kwargs={"decision_id": decision.id}))
    assert response.status_code == 404
