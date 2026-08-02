import pytest
from django.urls import reverse

from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.positions.models import Position
from apps.positions.services import submit_position


@pytest.mark.django_db
def test_finalisation_endpoint_returns_null_then_creates_record(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        proposed_by=decision.owner,
        created_by=decision.owner,
        title="Run a pilot",
        description="Test the approach for three months.",
    )
    submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=option.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="A pilot limits exposure.",
        confidence=Position.Confidence.HIGH,
    )
    api_client.force_authenticate(decision.owner)
    url = reverse("decisions:finalisation", kwargs={"decision_id": decision.id})

    assert api_client.get(url).json() == {"finalisation": None}
    response = api_client.post(
        url,
        {
            "expected_status": "ready_for_decision",
            "selected_option_id": str(option.id),
            "rationale": "Run the pilot and review the results.",
            "conditions": "Review after three months.",
            "dissent_summary": "",
            "positions_reviewed": True,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.json()["selected_option_id"] == str(option.id)
    assert api_client.get(url).json()["finalisation"]["id"] == response.json()["id"]


@pytest.mark.django_db
def test_finalisation_endpoint_rejects_unknown_field(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    api_client.force_authenticate(decision.owner)

    response = api_client.post(
        reverse("decisions:finalisation", kwargs={"decision_id": decision.id}),
        {
            "expected_status": "ready_for_decision",
            "selected_option_id": "00000000-0000-0000-0000-000000000001",
            "rationale": "Human rationale.",
            "positions_reviewed": True,
            "ai_decision": True,
        },
        format="json",
    )

    assert response.status_code == 400
    assert "ai_decision" in response.json()


@pytest.mark.django_db
def test_finalisation_endpoint_is_tenant_isolated(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)
    api_client.force_authenticate(user_factory())

    response = api_client.get(
        reverse("decisions:finalisation", kwargs={"decision_id": decision.id})
    )

    assert response.status_code == 404
