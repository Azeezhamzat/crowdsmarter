from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_personal_work_prioritises_overdue_assignments(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        status=Decision.Status.UNDER_REVIEW,
        target_decision_date=timezone.localdate() - timedelta(days=1),
    )
    api_client.force_authenticate(decision.owner)
    response = api_client.get(reverse("portfolio:personal-work"))
    assert response.status_code == 200
    assert response.json()["overdue_count"] == 1
    assert response.json()["decisions"][0]["id"] == str(decision.id)
    assert response.json()["decisions"][0]["is_overdue"] is True


@pytest.mark.django_db
def test_organisation_portfolio_filters_and_is_tenant_safe(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION, urgency="high")
    decision_factory(workspace=decision.workspace, status=Decision.Status.DRAFT, title="Other")
    url = reverse(
        "portfolio:organisation-portfolio",
        kwargs={"organisation_id": decision.organisation_id},
    )
    api_client.force_authenticate(decision.owner)
    response = api_client.get(url, {"status": Decision.Status.READY_FOR_DECISION})
    assert response.status_code == 200
    assert len(response.json()["decisions"]) == 1
    assert response.json()["decisions"][0]["title"] == decision.title

    api_client.force_authenticate(user_factory())
    assert api_client.get(url).status_code == 404


@pytest.mark.django_db
def test_portfolio_my_work_filter_uses_active_participation(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )
    api_client.force_authenticate(contributor)
    url = reverse(
        "portfolio:organisation-portfolio",
        kwargs={"organisation_id": decision.organisation_id},
    )
    response = api_client.get(url, {"my_work": "true"})
    assert response.status_code == 200
    assert [item["id"] for item in response.json()["decisions"]] == [str(decision.id)]
