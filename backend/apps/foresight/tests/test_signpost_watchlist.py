import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.urls import reverse

from apps.assumptions.services import create_assumption
from apps.decisions.models import Decision
from apps.foresight.mapping_services import create_canvas, create_driver
from apps.foresight.models import ForesightCanvas, Signal
from apps.foresight.scenario_services import (
    ScenarioServiceError,
    create_scenario_set,
    create_signpost,
    link_signpost_to_assumption,
    link_signpost_to_risk,
)
from apps.risks.services import create_risk


def _build_signpost(*, organisation, actor, decision=None):  # type: ignore[no-untyped-def]
    canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="Adaptive strategy canvas",
        focal_question="What could change our plan?",
        scope="A bounded system for watchlist testing.",
        horizon_year=2035,
        status=ForesightCanvas.Status.ACTIVE,
    )
    axis_x = create_driver(
        actor=actor,
        canvas=canvas,
        title="Axis X uncertainty",
        description="Could move either way.",
        driver_type="critical_uncertainty",
        steep_category=Signal.SteepCategory.ECONOMIC,
        impact=5,
        uncertainty=5,
    )
    axis_y = create_driver(
        actor=actor,
        canvas=canvas,
        title="Axis Y uncertainty",
        description="Could move either way.",
        driver_type="critical_uncertainty",
        steep_category=Signal.SteepCategory.SOCIAL,
        impact=5,
        uncertainty=5,
    )
    scenario_set = create_scenario_set(
        actor=actor,
        canvas=canvas,
        title="Watchlist scenario set",
        purpose="Exercise the adaptive-strategy watchlist.",
        axis_x_driver_id=axis_x.id,
        axis_x_low_label="Low",
        axis_x_high_label="High",
        axis_y_driver_id=axis_y.id,
        axis_y_low_label="Low",
        axis_y_high_label="High",
        linked_decision_id=decision.id if decision else None,
    )
    return create_signpost(
        actor=actor,
        scenario_set=scenario_set,
        title="Watchlist signpost",
        description="Tracks whether the plan should be revisited.",
        indicator="A concrete observable indicator",
        threshold="Exceeds the agreed trigger",
        direction="above",
        review_cadence="quarterly",
        scenario_links=[],
    )


@pytest.mark.django_db
def test_signpost_links_to_assumption_and_risk(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        status=Decision.Status.UNDER_REVIEW,
    )
    signpost = _build_signpost(organisation=organisation, actor=actor, decision=decision)
    assumption = create_assumption(
        actor=actor,
        decision=decision,
        statement="Demand keeps growing at the current rate.",
        impact_if_false="The plan would need to be scaled back.",
        confidence="medium",
    )
    risk = create_risk(
        actor=actor,
        decision=decision,
        title="Supplier concentration",
        description="Too few suppliers could bottleneck delivery.",
        likelihood=3,
        impact=4,
        response_strategy="monitor",
    )

    assumption_link = link_signpost_to_assumption(
        actor=actor,
        signpost=signpost,
        assumption_id=assumption.id,
        rationale="A sharp movement here would invalidate this assumption.",
    )
    risk_link = link_signpost_to_risk(
        actor=actor,
        signpost=signpost,
        risk_id=risk.id,
        rationale="This indicator is the leading warning sign for the risk.",
    )

    assert assumption_link.assumption == assumption
    assert risk_link.risk == risk
    assert signpost.assumption_links.count() == 1
    assert signpost.risk_links.count() == 1


@pytest.mark.django_db
def test_signpost_cannot_link_to_assumption_from_another_organisation(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    other_organisation = organisation_factory()
    other_decision = decision_factory(
        workspace=other_organisation.workspaces.get(is_default=True),
        owner=other_organisation.created_by,
        status=Decision.Status.UNDER_REVIEW,
    )
    foreign_assumption = create_assumption(
        actor=other_organisation.created_by,
        decision=other_decision,
        statement="A foreign assumption.",
        impact_if_false="Should not be linkable.",
        confidence="low",
    )
    signpost = _build_signpost(organisation=organisation, actor=actor)

    with pytest.raises(ScenarioServiceError):
        link_signpost_to_assumption(
            actor=actor,
            signpost=signpost,
            assumption_id=foreign_assumption.id,
            rationale="Should fail before reaching the database.",
        )


@pytest.mark.django_db
def test_only_contributor_can_link_signpost_watchlist(organisation_factory, user_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    outsider = user_factory()
    signpost = _build_signpost(organisation=organisation, actor=actor)

    with pytest.raises(PermissionDenied):
        link_signpost_to_risk(
            actor=outsider,
            signpost=signpost,
            risk_id="00000000-0000-0000-0000-000000000000",
            rationale="Should be rejected before the risk lookup.",
        )


@pytest.mark.django_db
def test_signpost_watchlist_link_requires_rationale(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        status=Decision.Status.UNDER_REVIEW,
    )
    signpost = _build_signpost(organisation=organisation, actor=actor, decision=decision)
    risk = create_risk(
        actor=actor,
        decision=decision,
        title="A risk",
        description="Needs a rationale to link.",
        likelihood=2,
        impact=2,
        response_strategy="accept",
    )

    with pytest.raises(ValidationError):
        link_signpost_to_risk(actor=actor, signpost=signpost, risk_id=risk.id, rationale="   ")


@pytest.mark.django_db
def test_signpost_watchlist_api_creates_links_and_exposes_them(
    api_client, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    api_client.force_authenticate(actor)
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        status=Decision.Status.UNDER_REVIEW,
    )
    signpost = _build_signpost(organisation=organisation, actor=actor, decision=decision)
    assumption = create_assumption(
        actor=actor,
        decision=decision,
        statement="A testable belief.",
        impact_if_false="Would change the approach.",
        confidence="high",
    )

    response = api_client.post(
        reverse("foresight:signpost-assumption-links", kwargs={"signpost_id": signpost.id}),
        {
            "assumption_id": str(assumption.id),
            "rationale": "This signpost is the clearest test of this assumption.",
        },
        format="json",
    )
    assert response.status_code == 201
    assert len(response.json()["assumption_links"]) == 1
    assert response.json()["assumption_links"][0]["assumption_id"] == str(assumption.id)

    unknown_field = api_client.post(
        reverse("foresight:signpost-assumption-links", kwargs={"signpost_id": signpost.id}),
        {
            "assumption_id": str(assumption.id),
            "rationale": "Repeat.",
            "extra": "not allowed",
        },
        format="json",
    )
    assert unknown_field.status_code == 400
    assert "extra" in unknown_field.json()
