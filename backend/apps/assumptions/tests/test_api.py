import pytest
from django.urls import reverse

from apps.decisions.models import Decision


@pytest.mark.django_db
def test_assumption_api_create_list_and_verify(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    collection = reverse("assumptions:list-create", kwargs={"decision_id": decision.id})

    response = api_client.post(
        collection,
        {
            "statement": "Field staff can allocate two hours per week.",
            "rationale": "The pilot plan reserves this time.",
            "impact_if_false": "The pilot would need fewer sites or more staff.",
            "confidence": "medium",
            "verification_status": "unverified",
            "verification_notes": "",
        },
        format="json",
    )

    assert response.status_code == 201
    assert len(api_client.get(collection).json()) == 1
    detail = reverse("assumptions:detail", kwargs={"assumption_id": response.json()["id"]})
    patch = api_client.patch(
        detail,
        {
            "verification_status": "verified",
            "verification_notes": "The field team lead confirmed availability.",
        },
        format="json",
    )
    assert patch.status_code == 200
    assert patch.json()["verification_status"] == "verified"


@pytest.mark.django_db
def test_assumption_api_rejects_unknown_field(
    api_client,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    api_client.force_authenticate(decision.owner)
    response = api_client.post(
        reverse("assumptions:list-create", kwargs={"decision_id": decision.id}),
        {
            "statement": "A valid assumption statement.",
            "impact_if_false": "The intended outcome would be at risk.",
            "confidence": "medium",
            "ai_generated": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "ai_generated" in response.json()


@pytest.mark.django_db
def test_accountable_reviewer_can_update_assumption(
    api_client,
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.assumptions.models import Assumption
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=reviewer,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
        added_by=decision.owner,
    )
    assumption = Assumption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        statement="The field team can review alerts within one working day.",
        impact_if_false="Escalation rules and staffing would need to change.",
        confidence=Assumption.Confidence.MEDIUM,
        owner=reviewer,
        created_by=decision.owner,
    )

    api_client.force_authenticate(reviewer)
    response = api_client.patch(
        reverse("assumptions:detail", kwargs={"assumption_id": assumption.id}),
        {
            "verification_status": "verified",
            "verification_notes": "The field operations lead confirmed the rota.",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.json()["verification_status"] == "verified"
