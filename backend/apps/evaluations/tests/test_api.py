import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_evaluation_api_is_strict_and_tenant_safe(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id}),
        {
            "title": "Blind scorecard",
            "purpose": "Compare alternatives independently.",
            "method": "scorecard",
            "anonymity": "peer_anonymous",
            "blind_results_until_close": True,
            "quorum_count": 1,
            "approval_threshold": 60,
            "objection_threshold": 20,
            "owner_id": str(owner.id),
            "manufactured_consensus": True,
        },
        format="json",
    )
    assert response.status_code == 400
    assert "manufactured_consensus" in response.json()

    api_client.force_authenticate(user_factory())
    hidden = api_client.get(
        reverse("evaluations:decision-evaluations", kwargs={"decision_id": decision.id})
    )
    assert hidden.status_code == 404


@pytest.mark.django_db
def test_prioritisation_api_creates_portfolio(
    api_client, organisation_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    owner = organisation.created_by
    api_client.force_authenticate(owner)
    response = api_client.post(
        reverse("evaluations:prioritisation-portfolios", kwargs={"organisation_id": organisation.id}),
        {
            "title": "Annual investment portfolio",
            "purpose": "Choose initiatives within the delivery envelope.",
            "budget_limit": "100000.00",
            "capacity_limit": "12.00",
            "owner_id": str(owner.id),
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.json()["recommendation"]["warning"].startswith("This is an explainable")


@pytest.mark.django_db
def test_scoring_options_endpoint_blinds_titles_for_non_managers(
    api_client, organisation_factory, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    from apps.decision_options.services import create_option
    from apps.evaluations.services import create_exercise
    from apps.organisations.models import Membership
    from apps.participants.models import Participant

    organisation = organisation_factory()
    owner = organisation.created_by
    reviewer = user_factory(email="scoring-reviewer@example.com")
    Membership.objects.create(
        organisation=organisation, user=reviewer, role=Membership.Role.CONTRIBUTOR, status=Membership.Status.ACTIVE,
    )
    decision = decision_factory(workspace=organisation.workspaces.get(is_default=True), owner=owner)
    Participant.objects.create(
        organisation=organisation, decision=decision, user=reviewer, role=Participant.Role.CONTRIBUTOR, added_by=owner,
    )
    create_option(actor=owner, decision=decision, title="Named Applicant Org", description="d")
    exercise = create_exercise(
        actor=owner, decision=decision, owner_id=owner.id, title="Blind scorecard", purpose="p",
        method="scorecard", blind_applicant_identity=True, quorum_count=1,
    )

    api_client.force_authenticate(reviewer)
    response = api_client.get(
        reverse("evaluations:evaluation-scoring-options", kwargs={"exercise_id": exercise.id})
    )
    assert response.status_code == 200
    assert response.json()[0]["title"] == "Application A"
    assert response.json()[0]["blinded"] is True

    api_client.force_authenticate(owner)
    manager_response = api_client.get(
        reverse("evaluations:evaluation-scoring-options", kwargs={"exercise_id": exercise.id})
    )
    assert manager_response.json()[0]["title"] == "Named Applicant Org"
    assert manager_response.json()[0]["blinded"] is False
