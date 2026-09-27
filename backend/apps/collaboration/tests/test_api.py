import pytest
from django.urls import reverse

from apps.audit.services import record_event
from apps.collaboration.models import DiscussionEntry
from apps.collaboration.services import create_discussion_entry
from apps.decisions.models import Decision


@pytest.mark.django_db
def test_discussion_api_is_tenant_safe_and_strict(api_client, decision_factory, user_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    url = reverse(
        "collaboration:discussion-list-create",
        kwargs={"decision_id": decision.id},
    )
    api_client.force_authenticate(decision.owner)
    response = api_client.post(
        url,
        {
            "kind": "note",
            "body": "An attributable note.",
            "mentioned_user_ids": [],
            "unexpected": "rejected",
        },
        format="json",
    )
    assert response.status_code == 400

    response = api_client.post(
        url,
        {"kind": "note", "body": "An attributable note.", "mentioned_user_ids": []},
        format="json",
    )
    assert response.status_code == 201
    assert api_client.get(url).json()["can_contribute"] is True

    api_client.force_authenticate(user_factory())
    assert api_client.get(url).status_code == 404


@pytest.mark.django_db
def test_activity_contains_discussion_and_audit_events(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    create_discussion_entry(
        actor=decision.owner,
        decision=decision,
        kind=DiscussionEntry.Kind.QUESTION,
        body="What remains unresolved?",
    )
    record_event(
        action="decision.updated",
        object_type="decision",
        object_id=str(decision.id),
        actor=decision.owner,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id)},
    )
    api_client.force_authenticate(decision.owner)
    url = reverse("collaboration:decision-activity", kwargs={"decision_id": decision.id})
    response = api_client.get(url)
    assert response.status_code == 200
    sources = {item["source"] for item in response.json()}
    assert {"audit", "discussion"}.issubset(sources)
