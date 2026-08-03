import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.organisations.models import Membership
from apps.organisations.services import (
    OrganisationServiceError,
    add_membership,
    change_membership_role,
    create_organisation,
    remove_membership,
)
from apps.participants.models import Participant
from apps.participants.services import add_participant
from apps.workspaces.models import Workspace


@pytest.mark.django_db
def test_create_organisation_makes_actor_owner_and_audits(
    user_factory,
):  # type: ignore[no-untyped-def]
    actor = user_factory()
    organisation = create_organisation(actor=actor, name="Acme", slug="acme")

    membership = Membership.objects.get(organisation=organisation, user=actor)
    assert membership.role == Membership.Role.OWNER
    assert AuditEvent.objects.filter(
        organisation=organisation,
        actor=actor,
        action="organisation.created",
    ).exists()
    assert Workspace.objects.filter(
        organisation=organisation,
        is_default=True,
        slug="decisions",
    ).exists()

    from apps.billing.models import OrganisationSubscription

    subscription = OrganisationSubscription.objects.get(organisation=organisation)
    assert subscription.status == OrganisationSubscription.Status.TRIALING
    assert subscription.plan.key == "team"


@pytest.mark.django_db
def test_last_owner_cannot_be_demoted(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.get(organisation=organisation, user=owner)

    with pytest.raises(OrganisationServiceError, match="retain at least one"):
        change_membership_role(
            actor=owner,
            membership=membership,
            role=Membership.Role.ADMIN,
        )


@pytest.mark.django_db
def test_last_owner_cannot_be_removed(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.get(organisation=organisation, user=owner)

    with pytest.raises(OrganisationServiceError, match="retain at least one"):
        remove_membership(actor=owner, membership=membership)


@pytest.mark.django_db
def test_owner_can_transfer_accountability_before_leaving(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    first_owner = user_factory()
    second_owner = user_factory()
    organisation = organisation_factory(owner=first_owner)
    first_membership = Membership.objects.get(organisation=organisation, user=first_owner)

    add_membership(
        actor=first_owner,
        organisation=organisation,
        user=second_owner,
        role=Membership.Role.OWNER,
    )
    remove_membership(actor=first_owner, membership=first_membership)

    assert not Membership.objects.filter(id=first_membership.id).exists()
    assert Membership.objects.filter(
        organisation=organisation,
        user=second_owner,
        role=Membership.Role.OWNER,
    ).exists()


@pytest.mark.django_db
def test_admin_cannot_appoint_or_modify_owner(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    admin = user_factory()
    candidate = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=admin,
        role=Membership.Role.ADMIN,
    )

    with pytest.raises(PermissionDenied, match="Only an owner"):
        add_membership(
            actor=admin,
            organisation=organisation,
            user=candidate,
            role=Membership.Role.OWNER,
        )

    owner_membership = Membership.objects.get(organisation=organisation, user=owner)
    with pytest.raises(PermissionDenied, match="cannot modify an owner"):
        change_membership_role(
            actor=admin,
            membership=owner_membership,
            role=Membership.Role.ADMIN,
        )


@pytest.mark.django_db
def test_create_organisation_normalises_stable_identity(
    user_factory,
):  # type: ignore[no-untyped-def]
    actor = user_factory()
    organisation = create_organisation(
        actor=actor,
        name="  Acme Group  ",
        slug="ACME-GROUP",
    )

    assert organisation.name == "Acme Group"
    assert organisation.slug == "acme-group"


@pytest.mark.django_db
def test_service_rejects_unknown_membership_role(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    candidate = user_factory()
    organisation = organisation_factory(owner=owner)

    with pytest.raises(ValidationError):
        add_membership(
            actor=owner,
            organisation=organisation,
            user=candidate,
            role="unbounded-authority",
        )


@pytest.mark.django_db
def test_unfinished_decision_ownership_must_be_transferred_before_offboarding(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    organisation_owner = user_factory()
    departing_owner = user_factory()
    organisation = organisation_factory(owner=organisation_owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_owner,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(
        organisation=organisation,
        created_by=organisation_owner,
    )
    decision_factory(
        workspace=workspace,
        owner=departing_owner,
        created_by=organisation_owner,
    )

    with pytest.raises(OrganisationServiceError, match="Transfer.*ownership"):
        remove_membership(actor=organisation_owner, membership=membership)

    assert Membership.objects.filter(id=membership.id).exists()


@pytest.mark.django_db
def test_offboarding_soft_removes_non_owner_decision_participation(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    organisation_owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=organisation_owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(
        organisation=organisation,
        created_by=organisation_owner,
    )
    decision = decision_factory(
        workspace=workspace,
        owner=organisation_owner,
        created_by=organisation_owner,
    )
    participant = add_participant(
        actor=organisation_owner,
        decision=decision,
        user=departing_member,
        role=Participant.Role.REVIEWER,
    )

    remove_membership(actor=organisation_owner, membership=membership)

    participant.refresh_from_db()
    assert not Membership.objects.filter(id=membership.id).exists()
    assert participant.status == Participant.Status.REMOVED
    assert participant.removed_by == organisation_owner
    event = AuditEvent.objects.get(
        action="participant.removed",
        object_id=str(participant.id),
    )
    assert event.metadata["reason"] == "membership_removed"


@pytest.mark.django_db
def test_active_assumption_ownership_must_be_transferred_before_offboarding(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.assumptions.models import Assumption
    from apps.assumptions.services import create_assumption
    from apps.decisions.models import Decision

    organisation_owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=organisation_owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(
        organisation=organisation,
        created_by=organisation_owner,
    )
    decision = decision_factory(
        workspace=workspace,
        owner=organisation_owner,
        created_by=organisation_owner,
        status=Decision.Status.UNDER_REVIEW,
    )
    create_assumption(
        actor=organisation_owner,
        decision=decision,
        owner_id=departing_member.id,
        statement="Field staff will use the mobile workflow consistently.",
        impact_if_false="The pilot data would not represent normal operations.",
        confidence=Assumption.Confidence.MEDIUM,
    )

    with pytest.raises(OrganisationServiceError, match="active assumption ownership"):
        remove_membership(actor=organisation_owner, membership=membership)

    assert Membership.objects.filter(id=membership.id).exists()


@pytest.mark.django_db
def test_open_risk_ownership_must_be_transferred_before_offboarding(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.decisions.models import Decision
    from apps.risks.models import Risk
    from apps.risks.services import create_risk

    organisation_owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=organisation_owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(
        organisation=organisation,
        created_by=organisation_owner,
    )
    decision = decision_factory(
        workspace=workspace,
        owner=organisation_owner,
        created_by=organisation_owner,
        status=Decision.Status.UNDER_REVIEW,
    )
    create_risk(
        actor=organisation_owner,
        decision=decision,
        owner_id=departing_member.id,
        title="Participant recruitment delay",
        description="The pilot may start before enough participants consent.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MONITOR,
    )

    with pytest.raises(OrganisationServiceError, match="open risk ownership"):
        remove_membership(actor=organisation_owner, membership=membership)

    assert Membership.objects.filter(id=membership.id).exists()

@pytest.mark.django_db
def test_remove_member_requires_active_implementation_transfer(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    from datetime import timedelta

    from django.utils import timezone

    from apps.decision_options.models import DecisionOption
    from apps.decisions.models import Decision, DecisionFinalisation
    from apps.reviews.models import DecisionReview
    from apps.workspaces.models import Workspace

    owner = user_factory()
    implementation_owner = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=implementation_owner,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = Workspace.objects.get(organisation=organisation, is_default=True)
    decision = Decision.objects.create(
        organisation=organisation,
        workspace=workspace,
        title="Implementation accountability",
        owner=owner,
        created_by=owner,
        status=Decision.Status.COMMITMENT,
    )
    option = DecisionOption.objects.create(
        organisation=organisation,
        decision=decision,
        title="Proceed",
        description="Approved option.",
        proposed_by=owner,
        created_by=owner,
    )
    DecisionFinalisation.objects.create(
        organisation=organisation,
        decision=decision,
        selected_option=option,
        decided_by=owner,
        rationale="Proceed.",
        position_snapshot=[],
    )
    DecisionReview.objects.create(
        organisation=organisation,
        decision=decision,
        implementation_owner=implementation_owner,
        commitment_statement="Deliver the approved option.",
        success_measures="Measure the outcome.",
        review_due_date=timezone.localdate() + timedelta(days=30),
        commitment_rationale="Approved.",
        commitment_recorded_by=owner,
    )

    with pytest.raises(OrganisationServiceError, match="implementation ownership"):
        remove_membership(actor=owner, membership=membership)

@pytest.mark.django_db
def test_active_foresight_canvas_ownership_must_be_transferred_before_offboarding(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    from apps.foresight.mapping_services import create_canvas

    owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    create_canvas(
        actor=owner,
        organisation=organisation,
        owner_id=departing_member.id,
        title="Regional resilience inquiry",
        focal_question="How might the regional system change?",
        scope="The regional system and its operating environment.",
        horizon_year=2035,
        status="active",
    )

    with pytest.raises(
        OrganisationServiceError, match="active foresight canvas ownership"
    ):
        remove_membership(actor=owner, membership=membership)


@pytest.mark.django_db
def test_active_foresight_driver_ownership_must_be_transferred_before_offboarding(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    from apps.foresight.mapping_services import create_canvas, create_driver

    owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    canvas = create_canvas(
        actor=owner,
        organisation=organisation,
        title="Technology transition",
        focal_question="Which forces could reshape the transition?",
        scope="The organisation and its technology ecosystem.",
        horizon_year=2032,
    )
    create_driver(
        actor=owner,
        canvas=canvas,
        owner_id=departing_member.id,
        title="Availability of implementation capability",
        description="Internal capability affects the pace and quality of transition.",
        driver_type="driver",
        steep_category="technological",
        impact=4,
        uncertainty=3,
    )

    with pytest.raises(OrganisationServiceError, match="active driver ownership"):
        remove_membership(actor=owner, membership=membership)


@pytest.mark.django_db
def test_open_strategic_implication_ownership_must_be_transferred_before_offboarding(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    from apps.foresight.mapping_services import create_canvas, create_implication

    owner = user_factory()
    departing_member = user_factory()
    organisation = organisation_factory(owner=owner)
    membership = Membership.objects.create(
        organisation=organisation,
        user=departing_member,
        role=Membership.Role.CONTRIBUTOR,
    )
    canvas = create_canvas(
        actor=owner,
        organisation=organisation,
        title="Policy environment",
        focal_question="How could the policy environment affect our choices?",
        scope="Relevant policy actors, rules, and implementation conditions.",
        horizon_year=2030,
    )
    create_implication(
        actor=owner,
        canvas=canvas,
        owner_id=departing_member.id,
        title="Prepare a contingent compliance pathway",
        description="The organisation should retain an option for rapid compliance change.",
        implication_type="policy",
        priority=4,
    )

    with pytest.raises(
        OrganisationServiceError, match="open strategic implication ownership"
    ):
        remove_membership(actor=owner, membership=membership)



@pytest.mark.django_db
def test_pending_contribution_review_must_be_completed_before_offboarding(
    user_factory,
    organisation_factory,
    workspace_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.contributions.services import create_request, submit_request

    owner = user_factory(email="owner-contribution-offboarding@example.com")
    contributor = user_factory(email="contributor-offboarding@example.com")
    reviewer = user_factory(email="reviewer-offboarding@example.com")
    organisation = organisation_factory(owner=owner)
    contributor_membership = Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    reviewer_membership = Membership.objects.create(
        organisation=organisation,
        user=reviewer,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(organisation=organisation, created_by=owner)
    decision = decision_factory(
        workspace=workspace,
        owner=owner,
        created_by=owner,
        status="open_for_contribution",
    )
    add_participant(
        actor=owner,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
    )
    add_participant(
        actor=owner,
        decision=decision,
        user=reviewer,
        role=Participant.Role.REVIEWER,
    )
    request = create_request(
        actor=owner,
        decision=decision,
        assignee_id=contributor.id,
        reviewer_id=reviewer.id,
        kind="review",
        title="Review the submitted evidence note",
        instructions="Confirm that limitations and provenance are retained.",
    )
    submit_request(
        actor=contributor,
        request=request,
        body="The note retains source provenance and material limitations.",
    )

    with pytest.raises(OrganisationServiceError, match="pending contribution reviews"):
        remove_membership(actor=owner, membership=reviewer_membership)

    assert Membership.objects.filter(id=reviewer_membership.id).exists()
    assert Membership.objects.filter(id=contributor_membership.id).exists()
