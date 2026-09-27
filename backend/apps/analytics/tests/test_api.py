from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.decisions.models import Decision, DecisionTransition
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_analytics_explains_flow_metrics(api_client, decision_factory):  # type: ignore[no-untyped-def]
    open_decision = decision_factory(
        status=Decision.Status.UNDER_REVIEW,
        target_decision_date=timezone.localdate() - timedelta(days=1),
    )
    finalised = decision_factory(
        workspace=open_decision.workspace,
        status=Decision.Status.DECISION_FINALISED,
    )
    DecisionTransition.objects.create(
        decision=finalised,
        organisation=finalised.organisation,
        sequence=1,
        from_status=Decision.Status.READY_FOR_DECISION,
        to_status=Decision.Status.DECISION_FINALISED,
        actor=finalised.owner,
        rationale="Human decision recorded.",
    )
    api_client.force_authenticate(open_decision.owner)
    url = reverse(
        "analytics:organisation",
        kwargs={"organisation_id": open_decision.organisation_id},
    )
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json()["totals"]["decisions"] == 2
    assert response.json()["flow"]["overdue_target_decisions"] == 1
    assert "median_days_to_finalise" in response.json()["definitions"]

    monthly_trend = response.json()["flow"]["monthly_trend"]
    assert len(monthly_trend) == 6
    current_month = monthly_trend[-1]
    assert current_month["created"] == 2
    assert current_month["finalised"] == 1
    assert monthly_trend[0]["month"] < monthly_trend[-1]["month"]


@pytest.mark.django_db
def test_analytics_is_tenant_isolated(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(user_factory())
    url = reverse(
        "analytics:organisation",
        kwargs={"organisation_id": decision.organisation_id},
    )
    assert api_client.get(url).status_code == 404


@pytest.mark.django_db
def test_analytics_insight_generates_a_narrative_for_owner(api_client, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    api_client.force_authenticate(decision.owner)
    url = reverse(
        "analytics:organisation-insight",
        kwargs={"organisation_id": decision.organisation_id},
    )
    response = api_client.post(url)
    assert response.status_code == 200
    payload = response.json()
    assert payload["headline"]
    assert payload["provider_label"] == "Transparent rules review"
    assert payload["id"]
    assert payload["requested_by"]["id"] == str(decision.owner_id)

    history_url = reverse(
        "analytics:organisation-insight-history",
        kwargs={"organisation_id": decision.organisation_id},
    )
    history_response = api_client.get(history_url)
    assert history_response.status_code == 200
    history_payload = history_response.json()
    assert len(history_payload) == 1
    assert history_payload[0]["id"] == payload["id"]


@pytest.mark.django_db
def test_analytics_insight_is_forbidden_to_contributors(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    api_client.force_authenticate(contributor)
    url = reverse(
        "analytics:organisation-insight",
        kwargs={"organisation_id": decision.organisation_id},
    )
    assert api_client.post(url).status_code == 403


@pytest.mark.django_db
def test_analytics_insight_is_tenant_isolated(api_client, user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    api_client.force_authenticate(user_factory())
    url = reverse(
        "analytics:organisation-insight",
        kwargs={"organisation_id": decision.organisation_id},
    )
    assert api_client.post(url).status_code == 404
