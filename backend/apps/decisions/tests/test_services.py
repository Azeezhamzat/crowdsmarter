from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.decisions.services import (
    DecisionServiceError,
    create_decision,
    transition_decision,
    update_decision,
)
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.participants.services import add_participant


@pytest.mark.django_db
def test_contributor_creates_owned_draft_with_owner_participant(
    user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    workspace = workspace_factory(organisation=organisation, created_by=owner)

    decision = create_decision(
        actor=contributor,
        workspace=workspace,
        title="Select a supplier",
        decision_question="Which supplier best meets our needs?",
    )

    assert decision.status == Decision.Status.DRAFT
    assert decision.owner == contributor
    assert Participant.objects.filter(
        decision=decision,
        user=contributor,
        role=Participant.Role.DECISION_OWNER,
    ).exists()
    assert AuditEvent.objects.filter(action="decision.created", object_id=str(decision.id)).exists()


@pytest.mark.django_db
def test_viewer_cannot_create_decision(
    user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    viewer = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(organisation=organisation, user=viewer, role=Membership.Role.VIEWER)
    workspace = workspace_factory(organisation=organisation, created_by=owner)

    with pytest.raises(PermissionDenied):
        create_decision(actor=viewer, workspace=workspace, title="Not permitted")


@pytest.mark.django_db
def test_contributor_cannot_assign_another_owner(
    user_factory, organisation_factory, workspace_factory
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    colleague = user_factory()
    organisation = organisation_factory(owner=owner)
    for user in (contributor, colleague):
        Membership.objects.create(
            organisation=organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
        )
    workspace = workspace_factory(organisation=organisation, created_by=owner)

    with pytest.raises(PermissionDenied, match="only create decisions they own"):
        create_decision(
            actor=contributor,
            workspace=workspace,
            title="Ownership rule",
            owner_id=colleague.id,
        )


@pytest.mark.django_db
def test_only_owner_or_manager_can_edit_draft(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    other_contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=other_contributor,
        role=Membership.Role.CONTRIBUTOR,
    )

    with pytest.raises(PermissionDenied):
        update_decision(
            actor=other_contributor,
            decision=decision,
            fields={"purpose": "Unauthorised change"},
        )


@pytest.mark.django_db
def test_draft_to_framing_requires_complete_frame(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(decision_question="")

    with pytest.raises(DecisionServiceError) as exc_info:
        transition_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.DRAFT,
            rationale="",
        )

    assert "decision_question" in exc_info.value.message_dict
    assert "purpose" in exc_info.value.message_dict
    assert "scope" in exc_info.value.message_dict


@pytest.mark.django_db
def test_lifecycle_reaches_under_review_with_history(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Which operating model should we adopt?",
        purpose="Choose a model that improves accountability.",
        scope="The customer operations function.",
        contribution_guidance="Contribute evidence about cost, speed, and service quality.",
        contribution_deadline=timezone.now() + timedelta(days=7),
    )
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )
    add_participant(
        actor=decision.owner,
        decision=decision,
        user=stakeholder,
        role=Participant.Role.CONTRIBUTOR,
    )

    first = transition_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.DRAFT,
        rationale="The initial frame is complete.",
    )
    decision.refresh_from_db()
    second = transition_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.FRAMING,
        rationale="Relevant contributors have been identified.",
    )
    decision.refresh_from_db()
    third = transition_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.OPEN_FOR_CONTRIBUTION,
        rationale="The contribution window has closed.",
    )
    decision.refresh_from_db()

    assert [first.sequence, second.sequence, third.sequence] == [1, 2, 3]
    assert decision.status == Decision.Status.UNDER_REVIEW
    assert decision.transitions.count() == 3
    assert (
        AuditEvent.objects.filter(
            action="decision.transitioned",
            object_id=str(decision.id),
        ).count()
        == 3
    )


@pytest.mark.django_db
def test_stale_transition_command_is_rejected(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(
        decision_question="Question?",
        purpose="Purpose.",
        scope="Scope.",
    )

    with pytest.raises(DecisionServiceError, match="changed after this page"):
        transition_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.FRAMING,
            rationale="",
        )


@pytest.mark.django_db
def test_review_to_ready_requires_structured_reasoning(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)

    with pytest.raises(DecisionServiceError) as exc_info:
        transition_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.UNDER_REVIEW,
            rationale="The review is complete.",
        )

    assert set(exc_info.value.message_dict) == {
        "options",
        "evidence",
        "assumptions",
        "risks",
    }


@pytest.mark.django_db
def test_phase_three_lifecycle_reaches_ready_for_decision(
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.assumptions.models import Assumption
    from apps.assumptions.services import create_assumption
    from apps.decision_options.services import create_option
    from apps.evidence.models import Evidence
    from apps.evidence.services import create_evidence
    from apps.risks.models import Risk
    from apps.risks.services import create_risk

    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    for title in ("Run a limited pilot", "Continue current practice"):
        create_option(
            actor=decision.owner,
            decision=decision,
            title=title,
            description=f"Detailed description for {title.lower()}.",
            is_status_quo=title.startswith("Continue"),
        )
    create_evidence(
        actor=decision.owner,
        decision=decision,
        title="Pilot benchmark",
        summary="Comparable pilots improved detection lead time.",
        source_type=Evidence.SourceType.RESEARCH,
        source_reference="Benchmark report 2026",
        stance=Evidence.Stance.SUPPORTS,
    )
    create_assumption(
        actor=decision.owner,
        decision=decision,
        statement="Field staff can support the pilot workload.",
        impact_if_false="The pilot scope would need to be reduced.",
        confidence=Assumption.Confidence.MEDIUM,
    )
    create_risk(
        actor=decision.owner,
        decision=decision,
        title="Low staff adoption",
        description="The tool may not fit the field workflow.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MITIGATE,
        mitigation_plan="Involve field staff in configuration and training.",
    )

    transition = transition_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.UNDER_REVIEW,
        rationale="The alternatives and uncertainties have been reviewed.",
    )
    decision.refresh_from_db()

    assert transition.to_status == Decision.Status.READY_FOR_DECISION
    assert decision.status == Decision.Status.READY_FOR_DECISION


@pytest.mark.django_db
def test_generic_transition_cannot_bypass_finalisation(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.READY_FOR_DECISION)

    with pytest.raises(DecisionServiceError, match="human finalisation command"):
        transition_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.READY_FOR_DECISION,
            rationale="Finalise",
        )


@pytest.mark.django_db
def test_manager_transfers_decision_ownership_and_participant_authority(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    organisation_owner = decision.organisation.created_by
    new_owner = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=new_owner,
        role=Membership.Role.CONTRIBUTOR,
    )

    updated = update_decision(
        actor=organisation_owner,
        decision=decision,
        fields={"owner_id": new_owner.id},
    )

    assert updated.owner == new_owner
    assert Participant.objects.filter(
        decision=decision,
        user=new_owner,
        role=Participant.Role.DECISION_OWNER,
        status=Participant.Status.ACTIVE,
    ).exists()
    assert Participant.objects.filter(
        decision=decision,
        user=organisation_owner,
        role=Participant.Role.CONTRIBUTOR,
        status=Participant.Status.ACTIVE,
    ).exists()
    assert Membership.objects.filter(
        organisation=decision.organisation,
        user=organisation_owner,
        role=Membership.Role.OWNER,
        status=Membership.Status.ACTIVE,
    ).exists()

@pytest.mark.django_db
def test_post_decision_transition_uses_dedicated_outcome_workflow(
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.decisions.services import available_transition

    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    transition = available_transition(decision)

    assert transition is not None
    assert transition["to_status"] == Decision.Status.COMMITMENT
    assert transition["enabled"] is True
    assert transition["action"] == "outcome_workflow"
