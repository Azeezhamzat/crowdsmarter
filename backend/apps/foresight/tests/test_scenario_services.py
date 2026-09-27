import pytest
from django.core.exceptions import ValidationError

from apps.audit.models import AuditEvent
from apps.decision_options.services import create_option
from apps.foresight.mapping_services import create_canvas, create_driver, create_implication
from apps.foresight.models import Driver, ForesightCanvas, ScenarioSet, Signal
from apps.foresight.scenario_services import (
    assess_option,
    create_scenario,
    create_scenario_set,
    create_signpost,
    create_signpost_observation,
    link_scenario_implication,
    set_scenario_driver_state,
    submit_scenario_review,
    update_scenario_set,
)


@pytest.mark.django_db
def test_team_builds_scenarios_tests_option_and_records_signpost(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="Future regional food resilience",
        focal_question="How could climate finance and automation reshape resilience by 2040?",
        scope="Regional production, finance, labour, technology, and policy.",
        horizon_year=2040,
        status=ForesightCanvas.Status.ACTIVE,
    )
    finance = create_driver(
        actor=actor,
        canvas=canvas,
        title="Access to affordable transition finance",
        description="Capital access determines who can invest in adaptation.",
        driver_type=Driver.DriverType.CRITICAL_UNCERTAINTY,
        steep_category=Signal.SteepCategory.ECONOMIC,
        direction=Driver.Direction.VOLATILE,
        impact=5,
        uncertainty=5,
    )
    automation = create_driver(
        actor=actor,
        canvas=canvas,
        title="Accessibility of trustworthy automation",
        description="Cost, reliability, and service access shape adoption.",
        driver_type=Driver.DriverType.CRITICAL_UNCERTAINTY,
        steep_category=Signal.SteepCategory.TECHNOLOGICAL,
        direction=Driver.Direction.INCREASING,
        impact=5,
        uncertainty=4,
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        title="Regional resilience investment strategy",
    )
    option = create_option(
        actor=actor,
        decision=decision,
        title="Distributed adaptation fund",
        description="Fund locally governed adaptation and shared technology access.",
    )
    scenario_set = create_scenario_set(
        actor=actor,
        canvas=canvas,
        title="Resilience pathways 2040",
        purpose="Stress-test the regional investment strategy across plausible futures.",
        axis_x_driver_id=finance.id,
        axis_x_low_label="Restricted finance",
        axis_x_high_label="Inclusive finance",
        axis_y_driver_id=automation.id,
        axis_y_low_label="Concentrated automation",
        axis_y_high_label="Accessible automation",
        linked_decision_id=decision.id,
        status=ScenarioSet.Status.ACTIVE,
    )
    scenario = create_scenario(
        actor=actor,
        scenario_set=scenario_set,
        title="Open capability commons",
        code="OC",
        axis_x_position="high",
        axis_y_position="high",
        headline="Finance and automation access reinforce distributed resilience.",
        narrative="Local actors can finance adaptation and access trusted automation services.",
        key_assumptions="Blended finance scales and interoperability standards remain open.",
        opportunities="Shared infrastructure and regional learning accelerate.",
        threats="Poor governance could still concentrate benefits.",
    )
    set_scenario_driver_state(
        actor=actor,
        scenario=scenario,
        driver_id=finance.id,
        state="strengthening",
        salience=5,
        description="Inclusive finance becomes a central transition enabler.",
    )
    review = submit_scenario_review(
        actor=actor,
        scenario=scenario,
        plausibility=4,
        internal_consistency=5,
        distinctiveness=4,
        usefulness=5,
        confidence=4,
        comment="Useful for exposing governance and access conditions.",
    )
    assessment = assess_option(
        actor=actor,
        scenario=scenario,
        option_id=option.id,
        verdict="robust",
        desirability=5,
        feasibility=4,
        resilience=5,
        rationale="The option matches the distributed institutions in this world.",
        conditions_for_success="Transparent allocation and shared standards.",
        vulnerabilities="Capture by dominant intermediaries.",
        mitigations="Participatory oversight and staged release of funds.",
    )
    implication = create_implication(
        actor=actor,
        canvas=canvas,
        title="Build local governance capability before capital deployment",
        description="Distributed finance requires credible local allocation and oversight.",
        implication_type="capability",
        priority=5,
        linked_decision_id=decision.id,
        driver_ids=[finance.id],
    )
    link_scenario_implication(
        actor=actor,
        scenario=scenario,
        implication_id=implication.id,
        effect="amplifies",
        rationale="This world increases both the value and urgency of local governance.",
    )
    signpost = create_signpost(
        actor=actor,
        scenario_set=scenario_set,
        title="Share of adaptation lending reaching smaller producers",
        description="Tracks whether finance access is broadening beyond incumbent actors.",
        indicator="Percentage of adaptation lending issued to smaller producers",
        threshold="Exceeds 35% for two consecutive quarters",
        direction="above",
        review_cadence="quarterly",
        scenario_links=[
            {
                "scenario_id": scenario.id,
                "relationship": "supports",
                "rationale": "Broad lending access supports the inclusive-finance axis state.",
            }
        ],
    )
    observation = create_signpost_observation(
        actor=actor,
        signpost=signpost,
        observed_on="2031-06-30",
        value="29%",
        assessment="moderate",
        evidence="Two regional lenders expanded eligibility but the trigger is not yet met.",
    )

    assert review.scenario == scenario
    with pytest.raises(ValidationError):
        update_scenario_set(
            actor=actor,
            scenario_set=scenario_set,
            fields={"linked_decision_id": None},
        )

    assert assessment.robustness_score == 4.67
    assert scenario.driver_states.count() == 1
    assert scenario.implication_links.count() == 1
    assert signpost.scenarios.get() == scenario
    assert observation.signpost == signpost
    assert (
        AuditEvent.objects.filter(
            organisation=organisation, action__startswith="foresight."
        ).count()
        >= 12
    )


@pytest.mark.django_db
def test_wind_tunnel_rejects_option_from_another_decision(organisation_factory, decision_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="Scenario boundary test",
        focal_question="How might the system change?",
        scope="One bounded system.",
        horizon_year=2035,
    )
    first = create_driver(
        actor=actor,
        canvas=canvas,
        title="First uncertainty",
        description="A material uncertainty.",
        driver_type="critical_uncertainty",
        steep_category="economic",
        impact=5,
        uncertainty=5,
    )
    second = create_driver(
        actor=actor,
        canvas=canvas,
        title="Second uncertainty",
        description="Another material uncertainty.",
        driver_type="critical_uncertainty",
        steep_category="political",
        impact=5,
        uncertainty=5,
    )
    linked_decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=actor
    )
    other_decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True), owner=actor
    )
    other_option = create_option(
        actor=actor,
        decision=other_decision,
        title="Wrong option",
        description="This option belongs to another decision.",
    )
    scenario_set = create_scenario_set(
        actor=actor,
        canvas=canvas,
        title="Boundary set",
        purpose="Validate decision-option boundaries.",
        axis_x_driver_id=first.id,
        axis_x_low_label="Low A",
        axis_x_high_label="High A",
        axis_y_driver_id=second.id,
        axis_y_low_label="Low B",
        axis_y_high_label="High B",
        linked_decision_id=linked_decision.id,
    )
    scenario = create_scenario(
        actor=actor,
        scenario_set=scenario_set,
        title="Boundary world",
        code="BW",
        axis_x_position="low",
        axis_y_position="low",
        headline="A bounded test world.",
        narrative="This scenario exists only to test tenant and decision boundaries.",
        key_assumptions="The linked decision remains fixed.",
    )

    with pytest.raises(ValidationError):
        assess_option(
            actor=actor,
            scenario=scenario,
            option_id=other_option.id,
            verdict="uncertain",
            desirability=3,
            feasibility=3,
            resilience=3,
            rationale="This must fail.",
        )
