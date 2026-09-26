from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision, DecisionFinalisation
from apps.organisations.models import Membership
from apps.reviews.models import DecisionReview
from apps.reviews.services import (
    ReviewServiceError,
    complete_outcome_review,
    open_outcome_review,
    record_commitment,
    start_implementation,
)


def finalised_decision(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    option = DecisionOption.objects.create(
        organisation=decision.organisation,
        decision=decision,
        title="Proceed",
        description="Proceed with the approved option.",
        proposed_by=decision.owner,
        created_by=decision.owner,
    )
    DecisionFinalisation.objects.create(
        organisation=decision.organisation,
        decision=decision,
        selected_option=option,
        decided_by=decision.owner,
        rationale="Human decision rationale.",
        position_snapshot=[],
    )
    return decision


@pytest.mark.django_db
def test_full_outcome_workflow_preserves_accountability(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = finalised_decision(decision_factory)
    review = record_commitment(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.DECISION_FINALISED,
        implementation_owner_id=decision.owner_id,
        commitment_statement="Run the approved pilot.",
        success_measures="Compare detection time and false positives.",
        review_due_date=timezone.localdate() + timedelta(days=90),
        rationale="The commitment reflects the selected option.",
    )
    decision.refresh_from_db()
    assert decision.status == Decision.Status.COMMITMENT
    assert review.implementation_owner == decision.owner

    start_implementation(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.COMMITMENT,
        implementation_plan="Start on three farms with weekly review.",
        rationale="People and safeguards are ready.",
    )
    decision.refresh_from_db()
    assert decision.status == Decision.Status.IMPLEMENTATION

    open_outcome_review(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.IMPLEMENTATION,
        implementation_summary="The three-farm pilot completed as planned.",
        rationale="Implementation evidence is available for review.",
    )
    decision.refresh_from_db()
    assert decision.status == Decision.Status.OUTCOME_REVIEW

    completed = complete_outcome_review(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.OUTCOME_REVIEW,
        outcome_summary="Detection was earlier on two farms and unchanged on one.",
        outcome_assessment=DecisionReview.OutcomeAssessment.PARTIALLY_MET,
        review_evidence="Inspection logs and farmer interviews.",
        unintended_consequences="Field staff needed additional training.",
        rationale="The evidence is sufficient to close the review.",
    )
    decision.refresh_from_db()
    assert decision.status == Decision.Status.LESSONS_LEARNED
    assert completed.reviewed_by == decision.owner
    assert decision.transitions.count() == 4
    assert AuditEvent.objects.filter(action="decision.outcome_review_completed").exists()


@pytest.mark.django_db
def test_commitment_requires_finalisation_record(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    with pytest.raises(ReviewServiceError, match="finalisation record"):
        record_commitment(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.DECISION_FINALISED,
            implementation_owner_id=decision.owner_id,
            commitment_statement="Proceed.",
            success_measures="Measure the outcome.",
            review_due_date=timezone.localdate() + timedelta(days=30),
            rationale="Approved.",
        )


@pytest.mark.django_db
def test_contributor_cannot_advance_post_decision_workflow(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = finalised_decision(decision_factory)
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    with pytest.raises(PermissionDenied):
        record_commitment(
            actor=contributor,
            decision=decision,
            expected_status=Decision.Status.DECISION_FINALISED,
            implementation_owner_id=contributor.id,
            commitment_statement="Proceed.",
            success_measures="Measure the outcome.",
            review_due_date=timezone.localdate() + timedelta(days=30),
            rationale="Attempted command.",
        )


@pytest.mark.django_db
def test_stale_outcome_command_is_rejected(decision_factory):  # type: ignore[no-untyped-def]
    decision = finalised_decision(decision_factory)
    with pytest.raises(ReviewServiceError) as exc_info:
        record_commitment(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.COMMITMENT,
            implementation_owner_id=decision.owner_id,
            commitment_statement="Proceed.",
            success_measures="Measure the outcome.",
            review_due_date=timezone.localdate() + timedelta(days=30),
            rationale="Attempted stale command.",
        )
    assert "expected_status" in exc_info.value.message_dict


@pytest.mark.django_db
def test_implementation_owner_can_be_transferred(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    from apps.reviews.services import change_implementation_owner

    decision = finalised_decision(decision_factory)
    replacement = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=replacement,
        role=Membership.Role.CONTRIBUTOR,
    )
    review = record_commitment(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.DECISION_FINALISED,
        implementation_owner_id=decision.owner_id,
        commitment_statement="Run the approved pilot.",
        success_measures="Measure the outcome.",
        review_due_date=timezone.localdate() + timedelta(days=30),
        rationale="Approved.",
    )
    changed = change_implementation_owner(
        actor=decision.owner,
        decision=decision,
        implementation_owner_id=replacement.id,
    )
    assert changed.id == review.id
    assert changed.implementation_owner == replacement
    assert AuditEvent.objects.filter(action="decision.implementation_owner_changed").exists()
