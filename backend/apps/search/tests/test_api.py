import pytest
from django.urls import reverse

from apps.decisions.models import Decision
from apps.lessons.models import Lesson


@pytest.mark.django_db
def test_search_finds_tenant_decisions_and_lessons(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        status=Decision.Status.LESSONS_LEARNED,
        title="Crop monitoring pilot",
        decision_question="Should we test earlier pest detection?",
        context="The organisation needs reliable crop protection evidence.",
    )
    Lesson.objects.create(
        organisation=decision.organisation,
        decision=decision,
        title="Capture baseline detection times",
        insight="Baseline evidence made the pest-monitoring outcome interpretable.",
        category=Lesson.Category.EVIDENCE,
        applicability="Future crop monitoring pilots.",
        created_by=decision.owner,
    )
    api_client.force_authenticate(decision.owner)
    url = reverse(
        "search:organisation-search",
        kwargs={"organisation_id": decision.organisation_id},
    )
    response = api_client.get(url, {"q": "pest monitoring"})
    assert response.status_code == 200
    kinds = {item["kind"] for item in response.json()["results"]}
    assert "decision" in kinds
    assert "lesson" in kinds


@pytest.mark.django_db
def test_search_does_not_reveal_another_tenant(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(title="Confidential acquisition decision")
    outsider = user_factory()
    api_client.force_authenticate(outsider)
    url = reverse(
        "search:organisation-search",
        kwargs={"organisation_id": decision.organisation_id},
    )
    assert api_client.get(url, {"q": "acquisition"}).status_code == 404


@pytest.mark.django_db
def test_search_requires_meaningful_query(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(decision.owner)
    url = reverse(
        "search:organisation-search",
        kwargs={"organisation_id": decision.organisation_id},
    )
    assert api_client.get(url, {"q": "a"}).status_code == 400
