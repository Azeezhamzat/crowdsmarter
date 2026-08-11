from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.assumptions.services import create_assumption
from apps.decisions.models import Decision
from apps.foresight.mapping_services import create_canvas, create_driver
from apps.foresight.models import ForesightCanvas, Signal
from apps.foresight.scenario_services import (
    create_scenario_set,
    create_signpost,
    create_signpost_observation,
)
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.reviews.models import DecisionReview
from apps.risks.services import create_risk


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


@pytest.mark.django_db
def test_organisation_portfolio_reports_a_watchlist(
    api_client, decision_factory
):  # type: ignore[no-untyped-def]
    stalled = decision_factory(status=Decision.Status.UNDER_REVIEW, title="Stalled decision")
    Decision.objects.filter(id=stalled.id).update(
        updated_at=timezone.now() - timedelta(days=30)
    )
    owner = stalled.owner
    risky_decision = decision_factory(
        workspace=stalled.workspace, owner=owner, status=Decision.Status.UNDER_REVIEW,
        title="Decision with a high risk",
    )
    create_risk(
        actor=owner, decision=risky_decision, title="Severe supplier risk",
        description="Could halt delivery entirely.", likelihood=5, impact=5,
        response_strategy="monitor",
    )
    assumption_decision = decision_factory(
        workspace=stalled.workspace, owner=owner, status=Decision.Status.UNDER_REVIEW,
        title="Decision with an at-risk assumption",
    )
    create_assumption(
        actor=owner, decision=assumption_decision,
        statement="An assumption overdue for re-verification.",
        impact_if_false="The plan would need to change.", confidence="medium",
        review_date=timezone.localdate() - timedelta(days=1),
    )
    reviewed_decision = decision_factory(
        workspace=stalled.workspace, owner=owner, status=Decision.Status.LESSONS_LEARNED,
        title="Decision with a completed outcome review",
    )
    DecisionReview.objects.create(
        organisation=reviewed_decision.organisation, decision=reviewed_decision,
        implementation_owner=owner, commitment_statement="Deliver the pilot.",
        success_measures="Measure adoption.",
        review_due_date=timezone.localdate() - timedelta(days=10),
        commitment_rationale="Human commitment.", commitment_recorded_by=owner,
        outcome_assessment=DecisionReview.OutcomeAssessment.MET,
    )
    canvas = create_canvas(
        actor=owner, organisation=stalled.organisation,
        title="Watchlist canvas", focal_question="What could change the plan?",
        scope="A bounded verification system.", horizon_year=2035,
        status=ForesightCanvas.Status.ACTIVE,
    )
    axis_x = create_driver(actor=owner, canvas=canvas, title="Axis X", description="Moves either way.", driver_type="critical_uncertainty", steep_category=Signal.SteepCategory.ECONOMIC, impact=5, uncertainty=5)
    axis_y = create_driver(actor=owner, canvas=canvas, title="Axis Y", description="Moves either way.", driver_type="critical_uncertainty", steep_category=Signal.SteepCategory.SOCIAL, impact=5, uncertainty=5)
    scenario_set = create_scenario_set(
        actor=owner, canvas=canvas, title="Watchlist scenario set", purpose="Exercise the watchlist.",
        axis_x_driver_id=axis_x.id, axis_x_low_label="Low", axis_x_high_label="High",
        axis_y_driver_id=axis_y.id, axis_y_low_label="Low", axis_y_high_label="High",
    )
    signpost = create_signpost(
        actor=owner, scenario_set=scenario_set, title="Watchlist signpost",
        description="Tracks whether the plan should be revisited.",
        indicator="A concrete observable indicator", threshold="Exceeds the agreed trigger",
        direction="above", review_cadence="quarterly", scenario_links=[],
    )
    create_signpost_observation(
        actor=owner, signpost=signpost, observed_on=timezone.localdate().isoformat(),
        value="Well past the threshold.", assessment="strong",
        evidence="Independent data confirms the movement.",
    )

    url = reverse(
        "portfolio:organisation-portfolio",
        kwargs={"organisation_id": stalled.organisation_id},
    )
    api_client.force_authenticate(owner)
    response = api_client.get(url)
    assert response.status_code == 200
    watchlist = response.json()["watchlist"]

    assert [item["id"] for item in watchlist["stalled_decisions"]] == [str(stalled.id)]
    assert watchlist["stalled_decisions"][0]["days_stalled"] >= 30

    heatmap = watchlist["risk_heatmap"]
    assert heatmap["total_open_risks"] == 1
    top_cell = next(cell for cell in heatmap["cells"] if cell["likelihood"] == 5 and cell["impact"] == 5)
    assert top_cell["count"] == 1
    assert top_cell["risks"][0]["decision_id"] == str(risky_decision.id)
    empty_cell = next(cell for cell in heatmap["cells"] if cell["likelihood"] == 1 and cell["impact"] == 1)
    assert empty_cell["count"] == 0
    assert len(heatmap["cells"]) == 25

    assert [item["decision_id"] for item in watchlist["open_high_risks"]] == [str(risky_decision.id)]

    assert [item["decision_id"] for item in watchlist["assumptions_at_risk"]] == [str(assumption_decision.id)]

    assert len(watchlist["triggered_signposts"]) == 1
    assert watchlist["triggered_signposts"][0]["signpost_id"] == str(signpost.id)

    assert watchlist["benefits_realization"]["met"] == 1
    assert watchlist["benefits_realization"]["total_reviewed"] == 1


@pytest.mark.django_db
def test_organisation_portfolio_watchlist_is_tenant_safe(
    api_client, decision_factory, user_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    create_risk(
        actor=decision.owner, decision=decision, title="A risk", description="Severe.",
        likelihood=5, impact=5, response_strategy="monitor",
    )
    url = reverse(
        "portfolio:organisation-portfolio",
        kwargs={"organisation_id": decision.organisation_id},
    )
    api_client.force_authenticate(user_factory())
    assert api_client.get(url).status_code == 404
