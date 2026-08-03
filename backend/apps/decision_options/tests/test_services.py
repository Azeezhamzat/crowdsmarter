import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decision_options.models import DecisionOption
from apps.decision_options.services import (
    DecisionOptionServiceError,
    create_option,
    update_option,
)
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_decision_owner_creates_and_withdraws_option(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)

    option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Run a limited pilot",
        description="Pilot on three sites for one season.",
        expected_benefits="Lower commitment while generating local evidence.",
    )
    update_option(
        actor=decision.owner,
        option=option,
        fields={"status": DecisionOption.Status.WITHDRAWN},
    )
    option.refresh_from_db()

    assert option.status == DecisionOption.Status.WITHDRAWN
    assert option.withdrawn_at is not None
    assert option.withdrawn_by == decision.owner
    assert AuditEvent.objects.filter(object_id=str(option.id)).count() == 2


@pytest.mark.django_db
def test_open_contributor_can_create_own_option(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
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

    option = create_option(
        actor=contributor,
        decision=decision,
        title="Alternative supplier",
        description="Use the lower-cost regional supplier.",
    )

    assert option.created_by == contributor


@pytest.mark.django_db
def test_viewer_cannot_create_option(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    viewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(PermissionDenied):
        create_option(
            actor=viewer,
            decision=decision,
            title="Not permitted",
            description="Viewers cannot contribute reasoning records.",
        )


@pytest.mark.django_db
def test_only_one_active_status_quo_option(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.FRAMING)
    create_option(
        actor=decision.owner,
        decision=decision,
        title="Continue current approach",
        description="Do not introduce a new process.",
        is_status_quo=True,
    )

    with pytest.raises(DecisionOptionServiceError, match="Only one active"):
        create_option(
            actor=decision.owner,
            decision=decision,
            title="Duplicate status quo",
            description="This duplicates the current-state alternative.",
            is_status_quo=True,
        )


@pytest.mark.django_db
def test_option_records_cost_and_implementation_estimates(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)

    option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Managed platform",
        description="Adopt a vendor-managed platform rather than building in-house.",
        estimated_cost="45000.00",
        cost_notes="First-year licence and onboarding.",
        implementation_time_estimate="3-6 months",
        reversibility=DecisionOption.Reversibility.PARTIALLY_REVERSIBLE,
    )

    assert option.estimated_cost == pytest.approx(45000.00)
    assert option.reversibility == DecisionOption.Reversibility.PARTIALLY_REVERSIBLE


@pytest.mark.django_db
def test_option_dependencies_and_mutual_exclusivity(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    prerequisite = create_option(
        actor=decision.owner, decision=decision,
        title="Data migration", description="Migrate legacy records first.",
    )
    alternative = create_option(
        actor=decision.owner, decision=decision,
        title="Keep legacy system", description="Do not migrate at all.",
    )

    dependent = create_option(
        actor=decision.owner, decision=decision,
        title="New reporting suite", description="Requires migrated data to function.",
        depends_on_ids=[str(prerequisite.id)],
        mutually_exclusive_with_ids=[str(alternative.id)],
    )

    assert list(dependent.depends_on.all()) == [prerequisite]
    assert list(dependent.mutually_exclusive_with.all()) == [alternative]
    # Symmetrical relation is visible from the other side too.
    assert list(alternative.mutually_exclusive_with.all()) == [dependent]


@pytest.mark.django_db
def test_option_cannot_depend_on_itself(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(
        actor=decision.owner, decision=decision,
        title="Self-referential option", description="Will try to depend on itself.",
    )

    with pytest.raises(DecisionOptionServiceError, match="cannot reference itself"):
        update_option(
            actor=decision.owner,
            option=option,
            fields={"depends_on_ids": [str(option.id)]},
        )


@pytest.mark.django_db
def test_option_dependency_must_belong_to_same_decision(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    other_decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    foreign_option = create_option(
        actor=other_decision.owner, decision=other_decision,
        title="Belongs to a different decision", description="Should not be linkable.",
    )
    option = create_option(
        actor=decision.owner, decision=decision,
        title="Local option", description="Belongs to this decision.",
    )

    with pytest.raises(DecisionOptionServiceError, match="must belong to this decision"):
        update_option(
            actor=decision.owner,
            option=option,
            fields={"depends_on_ids": [str(foreign_option.id)]},
        )
