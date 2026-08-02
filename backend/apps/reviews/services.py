"""Transactional commands for commitment, implementation, and outcome review."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.policies import can_transition_decision
from apps.decisions.services import append_transition_record
from apps.organisations.models import Membership

from .models import DecisionReview


class ReviewServiceError(ValidationError):
    """Expected execution or outcome-review workflow failure."""


def _active_member(*, organisation_id: Any, user_id: Any) -> User:
    try:
        return Membership.objects.select_related("user").get(
            organisation_id=organisation_id,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).user
    except Membership.DoesNotExist as exc:
        raise ReviewServiceError(
            {"implementation_owner_id": "Select an active organisation member."}
        ) from exc


def _locked_decision(*, decision: Decision, expected_status: str, actor: User) -> Decision:
    current = Decision.objects.select_for_update().select_related(
        "organisation", "owner"
    ).get(id=decision.id)
    if not can_transition_decision(actor=actor, decision=current):
        raise PermissionDenied("You do not hold lifecycle authority for this decision.")
    if current.status != expected_status:
        raise ReviewServiceError(
            {
                "expected_status": (
                    "The decision changed after this page was loaded. Refresh and retry."
                )
            }
        )
    return current


@transaction.atomic
def record_commitment(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    implementation_owner_id: Any,
    commitment_statement: str,
    success_measures: str,
    review_due_date: Any,
    rationale: str,
) -> DecisionReview:
    """Create the accountable execution record and enter Commitment."""
    current = _locked_decision(
        decision=decision,
        expected_status=expected_status,
        actor=actor,
    )
    if current.status != Decision.Status.DECISION_FINALISED:
        raise ReviewServiceError(
            "Commitment can be recorded only after the decision is finalised."
        )
    if not hasattr(current, "finalisation"):
        raise ReviewServiceError(
            "The immutable human finalisation record is required before commitment."
        )
    if DecisionReview.objects.filter(decision=current).exists():
        raise ReviewServiceError("This decision already has a commitment record.")
    owner = _active_member(
        organisation_id=current.organisation_id,
        user_id=implementation_owner_id,
    )
    if review_due_date < timezone.localdate():
        raise ReviewServiceError(
            {"review_due_date": "The outcome-review date cannot be in the past."}
        )
    review = DecisionReview(
        organisation=current.organisation,
        decision=current,
        implementation_owner=owner,
        commitment_statement=commitment_statement,
        success_measures=success_measures,
        review_due_date=review_due_date,
        commitment_rationale=rationale,
        commitment_recorded_by=actor,
    )
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save()
    append_transition_record(
        decision=current,
        actor=actor,
        to_status=Decision.Status.COMMITMENT,
        rationale=rationale,
    )
    record_event(
        action="decision.commitment_recorded",
        object_type="decision_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "implementation_owner_id": str(owner.id),
            "review_due_date": review.review_due_date.isoformat(),
        },
    )
    return review


@transaction.atomic
def start_implementation(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    implementation_plan: str,
    rationale: str,
) -> DecisionReview:
    """Record the implementation plan and enter Implementation."""
    current = _locked_decision(
        decision=decision,
        expected_status=expected_status,
        actor=actor,
    )
    if current.status != Decision.Status.COMMITMENT:
        raise ReviewServiceError("Implementation can start only from Commitment.")
    try:
        review = DecisionReview.objects.select_for_update().get(decision=current)
    except DecisionReview.DoesNotExist as exc:
        raise ReviewServiceError("Record the commitment before implementation.") from exc
    if not rationale.strip():
        raise ReviewServiceError(
            {"rationale": "Record why implementation is ready to begin."}
        )
    review.implementation_plan = implementation_plan.strip()
    review.implementation_started_by = actor
    review.implementation_started_at = timezone.now()
    if not review.implementation_plan:
        raise ReviewServiceError(
            {"implementation_plan": "Record the implementation plan."}
        )
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save(
        update_fields=[
            "implementation_plan",
            "implementation_started_by",
            "implementation_started_at",
            "updated_at",
        ]
    )
    append_transition_record(
        decision=current,
        actor=actor,
        to_status=Decision.Status.IMPLEMENTATION,
        rationale=rationale,
    )
    record_event(
        action="decision.implementation_started",
        object_type="decision_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.id)},
    )
    return review


@transaction.atomic
def open_outcome_review(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    implementation_summary: str,
    rationale: str,
) -> DecisionReview:
    """Close active implementation and open evidence-based outcome review."""
    current = _locked_decision(
        decision=decision,
        expected_status=expected_status,
        actor=actor,
    )
    if current.status != Decision.Status.IMPLEMENTATION:
        raise ReviewServiceError("Outcome review can open only from Implementation.")
    try:
        review = DecisionReview.objects.select_for_update().get(decision=current)
    except DecisionReview.DoesNotExist as exc:
        raise ReviewServiceError("The execution record is missing.") from exc
    if not rationale.strip():
        raise ReviewServiceError(
            {"rationale": "Record why the work is ready for outcome review."}
        )
    review.implementation_summary = implementation_summary.strip()
    if not review.implementation_summary:
        raise ReviewServiceError(
            {"implementation_summary": "Summarise what was implemented."}
        )
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save(update_fields=["implementation_summary", "updated_at"])
    append_transition_record(
        decision=current,
        actor=actor,
        to_status=Decision.Status.OUTCOME_REVIEW,
        rationale=rationale,
    )
    record_event(
        action="decision.outcome_review_opened",
        object_type="decision_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.id)},
    )
    return review


@transaction.atomic
def complete_outcome_review(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    outcome_summary: str,
    outcome_assessment: str,
    review_evidence: str,
    unintended_consequences: str = "",
    rationale: str,
) -> DecisionReview:
    """Complete the human outcome assessment and enter Lessons Learned."""
    current = _locked_decision(
        decision=decision,
        expected_status=expected_status,
        actor=actor,
    )
    if current.status != Decision.Status.OUTCOME_REVIEW:
        raise ReviewServiceError("The review can complete only from Outcome Review.")
    try:
        review = DecisionReview.objects.select_for_update().get(decision=current)
    except DecisionReview.DoesNotExist as exc:
        raise ReviewServiceError("The outcome-review record is missing.") from exc
    review.outcome_summary = outcome_summary.strip()
    review.outcome_assessment = outcome_assessment
    review.review_evidence = review_evidence.strip()
    review.unintended_consequences = unintended_consequences.strip()
    review.reviewed_by = actor
    review.reviewed_at = timezone.now()
    errors: dict[str, str] = {}
    if not review.outcome_summary:
        errors["outcome_summary"] = "Record what actually happened."
    if not review.review_evidence:
        errors["review_evidence"] = "Record the evidence used for this assessment."
    if not rationale.strip():
        errors["rationale"] = "Record why the review is complete."
    if errors:
        raise ReviewServiceError(errors)
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save(
        update_fields=[
            "outcome_summary",
            "outcome_assessment",
            "review_evidence",
            "unintended_consequences",
            "reviewed_by",
            "reviewed_at",
            "updated_at",
        ]
    )
    append_transition_record(
        decision=current,
        actor=actor,
        to_status=Decision.Status.LESSONS_LEARNED,
        rationale=rationale,
    )
    record_event(
        action="decision.outcome_review_completed",
        object_type="decision_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "outcome_assessment": outcome_assessment,
        },
    )
    return review


@transaction.atomic
def change_implementation_owner(
    *, actor: User, decision: Decision, implementation_owner_id: Any
) -> DecisionReview:
    """Transfer post-decision accountability to another active tenant member."""
    current = Decision.objects.select_for_update().select_related(
        "organisation", "owner"
    ).get(id=decision.id)
    if not can_transition_decision(actor=actor, decision=current):
        raise PermissionDenied("You cannot transfer implementation ownership.")
    if current.status == Decision.Status.ARCHIVED:
        raise ReviewServiceError("Archived outcome records are read-only.")
    try:
        review = DecisionReview.objects.select_for_update().get(decision=current)
    except DecisionReview.DoesNotExist as exc:
        raise ReviewServiceError("Record the commitment before transferring ownership.") from exc
    owner = _active_member(
        organisation_id=current.organisation_id,
        user_id=implementation_owner_id,
    )
    previous_owner_id = review.implementation_owner_id
    review.implementation_owner = owner
    review.full_clean(validate_unique=False, validate_constraints=False)
    review.save(update_fields=["implementation_owner", "updated_at"])
    record_event(
        action="decision.implementation_owner_changed",
        object_type="decision_review",
        object_id=str(review.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "previous_owner_id": str(previous_owner_id),
            "implementation_owner_id": str(owner.id),
        },
    )
    return review
