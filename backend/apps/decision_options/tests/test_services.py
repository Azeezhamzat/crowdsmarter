import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decision_options.models import DecisionOption
from apps.decision_options.services import (
    DecisionOptionServiceError,
    budget_summary,
    create_option,
    organisation_budget_rollup,
    set_eligibility,
    set_outcome,
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


@pytest.mark.django_db
def test_manager_sets_eligibility(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(
        actor=decision.owner, decision=decision,
        title="Community grant application", description="Reduces post-harvest loss.",
    )

    option = set_eligibility(
        actor=decision.owner,
        option=option,
        eligibility_status=DecisionOption.EligibilityStatus.ELIGIBLE,
        eligibility_note="Meets published criteria.",
    )

    assert option.eligibility_status == DecisionOption.EligibilityStatus.ELIGIBLE
    assert option.eligibility_decided_at is not None
    assert option.eligibility_decided_by == decision.owner
    assert AuditEvent.objects.filter(action="decision_option.eligibility_set").exists()


@pytest.mark.django_db
def test_reviewer_can_set_eligibility_during_review(
    user_factory, decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation, user=reviewer, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation, decision=decision, user=reviewer,
        role=Participant.Role.REVIEWER, added_by=decision.owner,
    )

    option = set_eligibility(
        actor=reviewer, option=option, eligibility_status=DecisionOption.EligibilityStatus.INELIGIBLE,
    )

    assert option.eligibility_status == DecisionOption.EligibilityStatus.INELIGIBLE


@pytest.mark.django_db
def test_contributor_cannot_set_eligibility(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation, user=contributor, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation, decision=decision, user=contributor,
        role=Participant.Role.CONTRIBUTOR, added_by=decision.owner,
    )

    with pytest.raises(PermissionDenied):
        set_eligibility(
            actor=contributor, option=option, eligibility_status=DecisionOption.EligibilityStatus.ELIGIBLE,
        )


@pytest.mark.django_db
def test_manager_funds_option_with_amount(decision_factory):  # type: ignore[no-untyped-def]
    # set_outcome is deliberately status-independent (funding decisions happen
    # after finalisation, which MANAGER_WRITE_STATUSES excludes) - options are
    # created while under review, matching create_option's own gate.
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(
        actor=decision.owner, decision=decision, title="Grant application",
        description="Desc.", estimated_cost="5000.00",
    )

    option = set_outcome(
        actor=decision.owner, option=option,
        outcome_status=DecisionOption.OutcomeStatus.FUNDED, awarded_amount="4500.00",
        outcome_note="Partially funded to spread the pool further.",
    )

    assert option.outcome_status == DecisionOption.OutcomeStatus.FUNDED
    assert option.awarded_amount == pytest.approx(4500.00)
    assert option.outcome_decided_by == decision.owner


@pytest.mark.django_db
def test_funded_outcome_requires_amount(decision_factory):  # type: ignore[no-untyped-def]
    from django.core.exceptions import ValidationError

    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")

    with pytest.raises(ValidationError):
        set_outcome(
            actor=decision.owner, option=option, outcome_status=DecisionOption.OutcomeStatus.FUNDED,
        )


@pytest.mark.django_db
def test_reviewer_cannot_set_outcome(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation, user=reviewer, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    Participant.objects.create(
        organisation=decision.organisation, decision=decision, user=reviewer,
        role=Participant.Role.REVIEWER, added_by=decision.owner,
    )

    with pytest.raises(PermissionDenied):
        set_outcome(
            actor=reviewer, option=option, outcome_status=DecisionOption.OutcomeStatus.DECLINED,
        )


@pytest.mark.django_db
def test_budget_summary_totals_active_options(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    funded = create_option(
        actor=decision.owner, decision=decision, title="Funded app",
        description="Desc.", estimated_cost="1000.00",
    )
    set_outcome(
        actor=decision.owner, option=funded, outcome_status=DecisionOption.OutcomeStatus.FUNDED,
        awarded_amount="800.00",
    )
    declined = create_option(
        actor=decision.owner, decision=decision, title="Declined app",
        description="Desc.", estimated_cost="2000.00",
    )
    set_outcome(actor=decision.owner, option=declined, outcome_status=DecisionOption.OutcomeStatus.DECLINED)
    create_option(
        actor=decision.owner, decision=decision, title="Pending app",
        description="Desc.", estimated_cost="500.00",
    )

    summary = budget_summary(decision=decision)

    assert summary["requested_total"] == pytest.approx(3500.00)
    assert summary["awarded_total"] == pytest.approx(800.00)
    assert summary["funded_count"] == 1
    assert summary["declined_count"] == 1
    assert summary["pending_outcome_count"] == 1


@pytest.mark.django_db
def test_organisation_budget_rollup_aggregates_across_grant_rounds(decision_factory):  # type: ignore[no-untyped-def]
    round_one = decision_factory(status=Decision.Status.UNDER_REVIEW, source_template_key="grant_round")
    round_two = decision_factory(
        workspace=round_one.workspace, status=Decision.Status.UNDER_REVIEW, source_template_key="grant_round",
    )
    non_grant_decision = decision_factory(workspace=round_one.workspace, status=Decision.Status.UNDER_REVIEW)

    funded_one = create_option(
        actor=round_one.owner, decision=round_one, title="Well project", description="d", estimated_cost="1000.00",
    )
    set_outcome(actor=round_one.owner, option=funded_one, outcome_status=DecisionOption.OutcomeStatus.FUNDED, awarded_amount="800.00")
    funded_two = create_option(
        actor=round_two.owner, decision=round_two, title="School project", description="d", estimated_cost="2000.00",
    )
    set_outcome(actor=round_two.owner, option=funded_two, outcome_status=DecisionOption.OutcomeStatus.FUNDED, awarded_amount="1500.00")
    declined = create_option(
        actor=round_two.owner, decision=round_two, title="Declined project", description="d", estimated_cost="500.00",
    )
    set_outcome(actor=round_two.owner, option=declined, outcome_status=DecisionOption.OutcomeStatus.DECLINED)
    # An option on a non-grant-round decision must not be counted.
    other_option = create_option(
        actor=non_grant_decision.owner, decision=non_grant_decision, title="Unrelated", description="d", estimated_cost="9999.00",
    )
    set_outcome(actor=non_grant_decision.owner, option=other_option, outcome_status=DecisionOption.OutcomeStatus.FUNDED, awarded_amount="9999.00")

    rollup = organisation_budget_rollup(organisation=round_one.organisation)

    assert rollup["round_count"] == 2
    assert rollup["requested_total"] == pytest.approx(3500.00)
    assert rollup["awarded_total"] == pytest.approx(2300.00)
    assert rollup["funded_count"] == 2
    assert rollup["declined_count"] == 1
    assert len(rollup["monthly_trend"]) == 6
    assert sum(month["awarded_total"] for month in rollup["monthly_trend"]) == pytest.approx(2300.00)
