"""Transactional decision creation, framing, and lifecycle workflows."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.organisations.models import Membership
from apps.workspaces.models import Workspace

from .models import Decision, DecisionTransition
from .policies import (
    MANAGER_ROLES,
    can_create_decision,
    can_edit_decision,
    can_transition_decision,
)


class DecisionServiceError(ValidationError):
    """Expected validation failure in a decision workflow."""


NEXT_STATUS: dict[str, str] = {
    Decision.Status.DRAFT: Decision.Status.FRAMING,
    Decision.Status.FRAMING: Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.OPEN_FOR_CONTRIBUTION: Decision.Status.UNDER_REVIEW,
    Decision.Status.UNDER_REVIEW: Decision.Status.READY_FOR_DECISION,
    Decision.Status.READY_FOR_DECISION: Decision.Status.DECISION_FINALISED,
    Decision.Status.DECISION_FINALISED: Decision.Status.COMMITMENT,
    Decision.Status.COMMITMENT: Decision.Status.IMPLEMENTATION,
    Decision.Status.IMPLEMENTATION: Decision.Status.OUTCOME_REVIEW,
    Decision.Status.OUTCOME_REVIEW: Decision.Status.LESSONS_LEARNED,
    Decision.Status.LESSONS_LEARNED: Decision.Status.ARCHIVED,
}

ENABLED_FROM_STATUSES = {
    Decision.Status.DRAFT,
    Decision.Status.FRAMING,
    Decision.Status.OPEN_FOR_CONTRIBUTION,
    Decision.Status.UNDER_REVIEW,
}


def _active_membership(*, actor: User, organisation_id: Any) -> Membership:
    try:
        return Membership.objects.get(
            organisation_id=organisation_id,
            user=actor,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc


def _active_member(*, organisation_id: Any, user_id: Any) -> User:
    try:
        membership = Membership.objects.select_related("user").get(
            organisation_id=organisation_id,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise DecisionServiceError(
            {"owner_id": "The decision owner must be an active organisation member."}
        ) from exc
    return membership.user


def _normalise_fields(decision: Decision, fields: dict[str, Any]) -> None:
    for field, value in fields.items():
        setattr(decision, field, value)


def available_transition(decision: Decision) -> dict[str, Any] | None:
    """Describe the next lifecycle step and its required human command."""
    to_status = NEXT_STATUS.get(decision.status)
    if to_status is None:
        return None
    if decision.status == Decision.Status.READY_FOR_DECISION:
        action = "finalise"
    elif decision.status in {
        Decision.Status.DECISION_FINALISED,
        Decision.Status.COMMITMENT,
        Decision.Status.IMPLEMENTATION,
        Decision.Status.OUTCOME_REVIEW,
        Decision.Status.LESSONS_LEARNED,
    }:
        action = "outcome_workflow"
    else:
        action = "transition"
    enabled = decision.status in ENABLED_FROM_STATUSES or action in {
        "finalise",
        "outcome_workflow",
    }
    reason = ""
    return {
        "from_status": decision.status,
        "to_status": to_status,
        "enabled": enabled,
        "blocked_reason": reason,
        "action": action,
    }


@transaction.atomic
def create_decision(
    *,
    actor: User,
    workspace: Workspace,
    title: str,
    decision_question: str = "",
    owner_id: Any | None = None,
) -> Decision:
    """Create a draft decision and establish its human owner."""
    membership = _active_membership(actor=actor, organisation_id=workspace.organisation_id)
    if not can_create_decision(membership=membership):
        raise PermissionDenied("Your role cannot create decisions.")

    owner = actor if owner_id is None else _active_member(
        organisation_id=workspace.organisation_id,
        user_id=owner_id,
    )
    if membership.role == Membership.Role.CONTRIBUTOR and owner.id != actor.id:
        raise PermissionDenied("Contributors may only create decisions they own.")

    decision = Decision(
        organisation=workspace.organisation,
        workspace=workspace,
        title=title,
        decision_question=decision_question,
        owner=owner,
        created_by=actor,
    )
    decision.full_clean(validate_unique=False, validate_constraints=False)
    decision.save()

    from apps.participants.services import ensure_owner_participant

    ensure_owner_participant(decision=decision, owner=owner, actor=actor)
    record_event(
        action="decision.created",
        object_type="decision",
        object_id=str(decision.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "workspace_id": str(workspace.id),
            "title": decision.title,
            "owner_id": str(owner.id),
            "status": decision.status,
        },
    )
    return decision


@transaction.atomic
def update_decision(
    *,
    actor: User,
    decision: Decision,
    fields: dict[str, Any],
) -> Decision:
    """Update framing fields while the lifecycle still permits editing."""
    decision = Decision.objects.select_for_update().select_related(
        "organisation", "workspace", "owner"
    ).get(id=decision.id)
    if not can_edit_decision(actor=actor, decision=decision):
        raise PermissionDenied("You cannot edit this decision in its current state.")

    previous_owner_id = decision.owner_id
    if "owner_id" in fields:
        requested_owner_id = fields.pop("owner_id")
        owner = _active_member(
            organisation_id=decision.organisation_id,
            user_id=requested_owner_id,
        )
        actor_membership = _active_membership(
            actor=actor, organisation_id=decision.organisation_id
        )
        if actor_membership.role not in MANAGER_ROLES and decision.owner_id != actor.id:
            raise PermissionDenied(
                "Only the decision owner or a tenant manager may transfer ownership."
            )
        decision.owner = owner

    before = {
        field: getattr(decision, field).isoformat()
        if hasattr(getattr(decision, field), "isoformat") and getattr(decision, field) is not None
        else getattr(decision, field)
        for field in fields
    }
    if previous_owner_id != decision.owner_id:
        before["owner_id"] = str(previous_owner_id)

    _normalise_fields(decision, fields)
    decision.full_clean(exclude=["created_by"], validate_unique=False)
    update_fields = list(fields) + ["updated_at"]
    if previous_owner_id != decision.owner_id:
        update_fields.append("owner")
    decision.save(update_fields=update_fields)

    if previous_owner_id != decision.owner_id:
        from apps.participants.services import change_owner_participant

        change_owner_participant(decision=decision, owner=decision.owner, actor=actor)

    after = {
        field: getattr(decision, field).isoformat()
        if hasattr(getattr(decision, field), "isoformat") and getattr(decision, field) is not None
        else getattr(decision, field)
        for field in fields
    }
    if previous_owner_id != decision.owner_id:
        after["owner_id"] = str(decision.owner_id)
    record_event(
        action="decision.updated",
        object_type="decision",
        object_id=str(decision.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"before": before, "after": after},
    )
    return decision


def _validate_draft_to_framing(decision: Decision, rationale: str) -> None:
    errors: dict[str, str] = {}
    if not decision.decision_question:
        errors["decision_question"] = "A clear decision question is required."
    if not decision.purpose:
        errors["purpose"] = "The decision purpose is required."
    if not decision.scope:
        errors["scope"] = "The decision scope is required."
    if errors:
        raise DecisionServiceError(errors)


def _validate_framing_to_contribution(decision: Decision, rationale: str) -> None:
    from apps.participants.models import Participant

    errors: dict[str, str] = {}
    if not decision.contribution_guidance:
        errors["contribution_guidance"] = "Contribution boundaries are required."
    if decision.contribution_deadline is None:
        errors["contribution_deadline"] = "A contribution deadline is required."
    elif decision.contribution_deadline <= timezone.now():
        errors["contribution_deadline"] = "The contribution deadline must be in the future."
    stakeholder_count = Participant.objects.filter(
        decision=decision,
        status=Participant.Status.ACTIVE,
    ).exclude(role=Participant.Role.DECISION_OWNER).count()
    if stakeholder_count < 1:
        errors["participants"] = "Add at least one stakeholder before opening contribution."
    if errors:
        raise DecisionServiceError(errors)


def _validate_contribution_to_review(decision: Decision, rationale: str) -> None:
    if not rationale.strip():
        raise DecisionServiceError(
            {"rationale": "Record why ordinary contribution is being closed."}
        )


def _validate_review_to_ready(decision: Decision, rationale: str) -> None:
    from apps.assumptions.models import Assumption
    from apps.decision_options.models import DecisionOption
    from apps.evidence.models import Evidence
    from apps.risks.models import Risk

    errors: dict[str, str] = {}
    if not rationale.strip():
        errors["rationale"] = "Record why the structured review is complete."
    option_count = DecisionOption.objects.filter(
        decision=decision, status=DecisionOption.Status.ACTIVE
    ).count()
    if option_count < 2:
        errors["options"] = "At least two active options are required."
    if not Evidence.objects.filter(
        decision=decision, status=Evidence.Status.ACTIVE
    ).exists():
        errors["evidence"] = "Record at least one active evidence item."
    if not Assumption.objects.filter(
        decision=decision, status=Assumption.Status.ACTIVE
    ).exists():
        errors["assumptions"] = "Record at least one active assumption."
    if Assumption.objects.filter(
        decision=decision,
        status=Assumption.Status.ACTIVE,
        verification_status=Assumption.VerificationStatus.INVALIDATED,
    ).exists():
        errors["assumptions"] = (
            "Retire or resolve invalidated assumptions before readiness."
        )
    if not Risk.objects.filter(decision=decision).exclude(
        status=Risk.Status.CLOSED
    ).exists():
        errors["risks"] = "Record at least one current risk."
    if errors:
        raise DecisionServiceError(errors)


TRANSITION_VALIDATORS: dict[str, Callable[[Decision, str], None]] = {
    Decision.Status.DRAFT: _validate_draft_to_framing,
    Decision.Status.FRAMING: _validate_framing_to_contribution,
    Decision.Status.OPEN_FOR_CONTRIBUTION: _validate_contribution_to_review,
    Decision.Status.UNDER_REVIEW: _validate_review_to_ready,
}


def append_transition_record(
    *,
    decision: Decision,
    actor: User,
    to_status: str,
    rationale: str,
    warnings_acknowledged: list[str] | None = None,
) -> DecisionTransition:
    """Append lifecycle history and update a decision already locked by a workflow."""
    from_status = decision.status
    sequence = decision.transitions.count() + 1
    transition_record = DecisionTransition(
        decision=decision,
        organisation=decision.organisation,
        sequence=sequence,
        from_status=from_status,
        to_status=to_status,
        actor=actor,
        rationale=rationale.strip(),
        warnings_acknowledged=warnings_acknowledged or [],
    )
    transition_record.full_clean(validate_unique=False, validate_constraints=False)
    transition_record.save()
    decision.status = to_status
    decision.status_changed_at = timezone.now()
    decision.save(update_fields=["status", "status_changed_at", "updated_at"])
    record_event(
        action="decision.transitioned",
        object_type="decision",
        object_id=str(decision.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "transition_id": str(transition_record.id),
            "sequence": sequence,
            "from_status": from_status,
            "to_status": to_status,
            "rationale": transition_record.rationale,
            "warnings_acknowledged": transition_record.warnings_acknowledged,
        },
    )
    return transition_record


@transaction.atomic
def transition_decision(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    rationale: str,
    warnings_acknowledged: list[str] | None = None,
) -> DecisionTransition:
    """Advance exactly one authorised lifecycle step and preserve history."""
    decision = Decision.objects.select_for_update().select_related(
        "organisation", "owner"
    ).get(id=decision.id)
    if not can_transition_decision(actor=actor, decision=decision):
        raise PermissionDenied("You do not hold lifecycle authority for this decision.")
    if decision.status != expected_status:
        raise DecisionServiceError(
            {
                "expected_status": (
                    "The decision changed after this page was loaded. "
                    "Refresh and retry."
                )
            }
        )
    transition = available_transition(decision)
    if transition is None:
        raise DecisionServiceError("The archived state has no further transition.")
    if not transition["enabled"]:
        raise DecisionServiceError(transition["blocked_reason"])
    if transition["action"] == "finalise":
        raise DecisionServiceError(
            "Use the human finalisation command to select an option and finalise this decision."
        )
    if transition["action"] == "outcome_workflow":
        raise DecisionServiceError(
            "Use the accountable outcomes and learning workflow for this lifecycle step."
        )

    validator = TRANSITION_VALIDATORS[decision.status]
    validator(decision, rationale)
    return append_transition_record(
        decision=decision,
        actor=actor,
        to_status=transition["to_status"],
        rationale=rationale,
        warnings_acknowledged=warnings_acknowledged,
    )
