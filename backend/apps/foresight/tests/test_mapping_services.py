import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.foresight.mapping_services import (
    create_canvas,
    create_consequence,
    create_driver,
    create_feedback_loop,
    create_horizon_item,
    create_implication,
    create_relationship,
    create_stakeholder,
    link_signal_to_driver,
)
from apps.foresight.models import Driver, ForesightCanvas, Signal, Source
from apps.foresight.services import create_signal, create_source
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_contributor_builds_traceable_systems_canvas(
    user_factory, organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    contributor = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    source = create_source(
        actor=contributor,
        organisation=organisation,
        title="Climate-risk assessment",
        source_type=Source.SourceType.RESEARCH,
        source_url="https://example.org/climate",
        credibility=Source.Credibility.HIGH,
    )
    signal = create_signal(
        actor=contributor,
        organisation=organisation,
        source_id=source.id,
        title="Insurance coverage is retreating from high-risk regions",
        summary="Insurers are narrowing coverage in exposed agricultural regions.",
        future_implication="Investment and production choices may become harder to finance.",
        steep_category=Signal.SteepCategory.ECONOMIC,
        time_horizon=Signal.TimeHorizon.MEDIUM,
        maturity=Signal.Maturity.EMERGING,
        polarity=Signal.Polarity.THREAT,
        impact=4,
        uncertainty=4,
    )
    canvas = create_canvas(
        actor=contributor,
        organisation=organisation,
        title="Future resilience of regional agriculture",
        focal_question="How might climate, finance, and technology reshape regional agriculture?",
        scope="Regional food production, finance, regulation, and farm operations.",
        horizon_year=2035,
        status=ForesightCanvas.Status.ACTIVE,
    )
    finance = create_driver(
        actor=contributor,
        canvas=canvas,
        title="Availability of affordable risk finance",
        description="Insurance and lending conditions influence who can continue investing.",
        driver_type=Driver.DriverType.CRITICAL_UNCERTAINTY,
        steep_category=Signal.SteepCategory.ECONOMIC,
        direction=Driver.Direction.VOLATILE,
        impact=5,
        uncertainty=5,
    )
    adaptation = create_driver(
        actor=contributor,
        canvas=canvas,
        title="Adoption of climate-adaptive production",
        description="Farm-level adaptation can reduce losses and change finance risk assessments.",
        driver_type=Driver.DriverType.DRIVER,
        steep_category=Signal.SteepCategory.TECHNOLOGICAL,
        direction=Driver.Direction.INCREASING,
        impact=4,
        uncertainty=3,
    )
    link_signal_to_driver(
        actor=contributor,
        driver=finance,
        signal_id=signal.id,
        rationale="The signal is direct evidence that affordable coverage may contract.",
    )
    create_stakeholder(
        actor=contributor,
        canvas=canvas,
        name="Smallholder farmers",
        stakeholder_type="community",
        role="Produce food and make on-farm adaptation investments.",
        interests="Stable income, affordable finance, and manageable transition costs.",
        influence=3,
        exposure=5,
        stance="mixed",
    )
    create_relationship(
        actor=contributor,
        canvas=canvas,
        source_driver_id=adaptation.id,
        target_driver_id=finance.id,
        polarity="reinforcing",
        strength=4,
        delay="medium",
        rationale="Demonstrated adaptation can improve loss experience and insurer confidence.",
    )
    feedback_loop = create_feedback_loop(
        actor=contributor,
        canvas=canvas,
        name="Adaptation confidence loop",
        description=(
            "Visible adaptation can improve finance confidence, which enables further "
            "adaptation investment."
        ),
        loop_type="reinforcing",
        driver_ids=[adaptation.id, finance.id],
        rationale="The loop is grounded in the recorded causal relationship and signal.",
    )
    first = create_consequence(
        actor=contributor,
        canvas=canvas,
        originating_driver_id=finance.id,
        title="Investment concentrates among well-capitalised farms",
        description="Restricted finance may advantage actors able to self-fund adaptation.",
        consequence_type="threat",
        likelihood=4,
        impact=4,
    )
    create_consequence(
        actor=contributor,
        canvas=canvas,
        parent_id=first.id,
        title="Regional supplier networks become less diverse",
        description="Farm consolidation could reduce the number and diversity of local buyers.",
        consequence_type="mixed",
        likelihood=3,
        impact=3,
    )
    create_horizon_item(
        actor=contributor,
        canvas=canvas,
        horizon="h2",
        title="Blended adaptation finance",
        description="Public and private capital jointly de-risk transition investment.",
        evidence="Early pilots are visible in comparable regions.",
    )
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=organisation.created_by,
        title="Regional adaptation investment programme",
    )
    implication = create_implication(
        actor=contributor,
        canvas=canvas,
        title="Develop a finance-access decision before scaling the programme",
        description="The organisation should decide how finance access affects programme equity.",
        implication_type="decision_requirement",
        priority=5,
        linked_decision_id=decision.id,
        driver_ids=[finance.id, adaptation.id],
    )

    assert finance.signals.filter(id=signal.id).exists()
    assert implication.drivers.count() == 2
    assert canvas.relationships.count() == 1
    assert canvas.feedback_loops.count() == 1
    assert list(
        feedback_loop.driver_links.order_by("position").values_list("driver_id", flat=True)
    ) == [adaptation.id, finance.id]
    assert canvas.consequences.count() == 2
    assert (
        AuditEvent.objects.filter(
            organisation=organisation, action__startswith="foresight."
        ).count()
        >= 13
    )


@pytest.mark.django_db
def test_viewer_cannot_create_foresight_canvas(user_factory, organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    viewer = user_factory()
    Membership.objects.create(
        organisation=organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(PermissionDenied):
        create_canvas(
            actor=viewer,
            organisation=organisation,
            title="Not permitted",
            focal_question="What changes?",
            scope="A bounded system.",
            horizon_year=2035,
        )


@pytest.mark.django_db
def test_relationship_rejects_drivers_from_different_canvases(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    first_canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="First canvas",
        focal_question="What is changing in the first system?",
        scope="First system.",
        horizon_year=2035,
    )
    second_canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="Second canvas",
        focal_question="What is changing in the second system?",
        scope="Second system.",
        horizon_year=2040,
    )
    first = create_driver(
        actor=actor,
        canvas=first_canvas,
        title="First driver",
        description="A force in the first system.",
        driver_type="driver",
        steep_category="social",
        impact=3,
        uncertainty=3,
    )
    second = create_driver(
        actor=actor,
        canvas=second_canvas,
        title="Second driver",
        description="A force in the second system.",
        driver_type="driver",
        steep_category="economic",
        impact=3,
        uncertainty=3,
    )

    with pytest.raises(ValidationError):
        create_relationship(
            actor=actor,
            canvas=first_canvas,
            source_driver_id=first.id,
            target_driver_id=second.id,
            polarity="uncertain",
            strength=3,
            rationale="This invalid relationship crosses a canvas boundary.",
        )


@pytest.mark.django_db
def test_archived_canvas_is_read_only(organisation_factory):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    canvas = create_canvas(
        actor=organisation.created_by,
        organisation=organisation,
        title="Archived inquiry",
        focal_question="What happened?",
        scope="A completed inquiry.",
        horizon_year=2030,
        status=ForesightCanvas.Status.ARCHIVED,
    )

    with pytest.raises(ValidationError):
        create_driver(
            actor=organisation.created_by,
            canvas=canvas,
            title="Late addition",
            description="Archived canvases must not accept new interpretation.",
            driver_type="driver",
            steep_category="ethical",
            impact=2,
            uncertainty=2,
        )
