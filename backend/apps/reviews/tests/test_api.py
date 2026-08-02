from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision, DecisionFinalisation


def finalised_decision(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        title="Approved option",
        description="The selected option.",
        proposed_by=decision.owner,
        created_by=decision.owner,
    )
    DecisionFinalisation.objects.create(
        organisation=decision.organisation,
        decision=decision,
        selected_option=option,
        decided_by=decision.owner,
        rationale="Approved by a human.",
        position_snapshot=[],
    )
    return decision


@pytest.mark.django_db
def test_review_api_runs_all_post_decision_commands(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = finalised_decision(decision_factory)
    api_client.force_authenticate(decision.owner)
    commitment = reverse("reviews:commitment", kwargs={"decision_id": decision.id})
    response = api_client.post(
        commitment,
        {
            "expected_status": "decision_finalised",
            "implementation_owner_id": str(decision.owner_id),
            "commitment_statement": "Run the approved pilot.",
            "success_measures": "Compare service quality and trust.",
            "review_due_date": (timezone.localdate() + timedelta(days=60)).isoformat(),
            "rationale": "The record reflects the final decision.",
        },
        format="json",
    )
    assert response.status_code == 201
    detail = reverse("reviews:detail", kwargs={"decision_id": decision.id})
    assert api_client.get(detail).json()["review"]
    transfer = api_client.patch(
        detail,
        {"implementation_owner_id": str(decision.owner_id)},
        format="json",
    )
    assert transfer.status_code == 200

    response = api_client.post(
        reverse("reviews:implementation-start", kwargs={"decision_id": decision.id}),
        {
            "expected_status": "commitment",
            "implementation_plan": "Run a controlled sixty-day pilot.",
            "rationale": "Implementation safeguards are ready.",
        },
        format="json",
    )
    assert response.status_code == 200

    response = api_client.post(
        reverse("reviews:outcome-review-open", kwargs={"decision_id": decision.id}),
        {
            "expected_status": "implementation",
            "implementation_summary": "The pilot completed on schedule.",
            "rationale": "Outcome data is available.",
        },
        format="json",
    )
    assert response.status_code == 200

    response = api_client.post(
        reverse("reviews:outcome-review-complete", kwargs={"decision_id": decision.id}),
        {
            "expected_status": "outcome_review",
            "outcome_summary": "The pilot improved service quality.",
            "outcome_assessment": "met",
            "review_evidence": "Service records and interviews.",
            "unintended_consequences": "Additional training was needed.",
            "rationale": "The evidence is sufficient.",
        },
        format="json",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_review_api_is_tenant_isolated(
    api_client, user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = finalised_decision(decision_factory)
    api_client.force_authenticate(user_factory())
    response = api_client.get(reverse("reviews:detail", kwargs={"decision_id": decision.id}))
    assert response.status_code == 404
