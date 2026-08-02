import pytest
from django.urls import reverse

from apps.decision_options.services import create_option
from apps.decisions.models import Decision
from apps.positions.models import Position


@pytest.mark.django_db
def test_position_endpoint_submits_current_and_preserves_history(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Pilot",
        description="Run a limited pilot.",
    )
    api_client.force_authenticate(decision.owner)
    collection = reverse("positions:list-create", kwargs={"decision_id": decision.id})

    first = api_client.post(
        collection,
        {
            "preferred_option_id": str(option.id),
            "recommendation": "support",
            "rationale": "The pilot reduces exposure.",
            "confidence": "medium",
        },
        format="json",
    )
    second = api_client.post(
        collection,
        {
            "recommendation": "abstain",
            "rationale": "I need more information.",
            "confidence": "low",
        },
        format="json",
    )

    assert first.status_code == 201
    assert second.status_code == 201
    current = api_client.get(collection)
    history = api_client.get(
        reverse("positions:history", kwargs={"decision_id": decision.id})
    )
    assert current.status_code == 200
    assert len(current.json()) == 1
    assert current.json()[0]["version"] == 2
    assert history.status_code == 200
    assert len(history.json()) == 2


@pytest.mark.django_db
def test_position_endpoint_rejects_unknown_fields(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)

    response = api_client.post(
        reverse("positions:list-create", kwargs={"decision_id": decision.id}),
        {
            "recommendation": Position.Recommendation.ABSTAIN,
            "rationale": "Not enough information.",
            "confidence": Position.Confidence.LOW,
            "ai_selected": True,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "ai_selected" in response.json()


@pytest.mark.django_db
def test_position_endpoint_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(user_factory())

    response = api_client.get(
        reverse("positions:list-create", kwargs={"decision_id": decision.id})
    )

    assert response.status_code == 404
