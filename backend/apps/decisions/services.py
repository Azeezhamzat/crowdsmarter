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
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.workspaces.models import Workspace

from .models import Decision, DecisionTransition
from .policies import (
    MANAGER_ROLES,
    can_create_decision,
    can_edit_decision,
    can_transition_decision,
)
from .templates import template_for_key


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
    purpose: str = "",
    context: str = "",
    scope: str = "",
    contribution_guidance: str = "",
    urgency: str = Decision.Urgency.NORMAL,
    target_decision_date: Any | None = None,
    contribution_deadline: Any | None = None,
    template_key: str = "blank",
    method_version_id: Any | None = None,
    owner_id: Any | None = None,
) -> Decision:
    """Create a draft decision and establish its human owner."""
    membership = _active_membership(actor=actor, organisation_id=workspace.organisation_id)
    if workspace.organisation.status != "active":
        raise DecisionServiceError("Reactivate the organisation before creating a decision.")
    if not can_create_decision(membership=membership):
        raise PermissionDenied("Your role cannot create decisions.")

    owner = actor if owner_id is None else _active_member(
        organisation_id=workspace.organisation_id,
        user_id=owner_id,
    )
    if membership.role == Membership.Role.CONTRIBUTOR and owner.id != actor.id:
        raise PermissionDenied("Contributors may only create decisions they own.")

    selected_method_version = None
    selected_template = None
    if method_version_id:
        from apps.methodology.models import DecisionMethodVersion

        try:
            selected_method_version = DecisionMethodVersion.objects.select_related("method").get(
                id=method_version_id,
                organisation_id=workspace.organisation_id,
                status=DecisionMethodVersion.Status.APPROVED,
                method__status="approved",
            )
        except DecisionMethodVersion.DoesNotExist as exc:
            raise DecisionServiceError({"method_version_id": "Choose an approved organisation method."}) from exc
    else:
        selected_template = template_for_key(template_key)
        if selected_template is None:
            raise DecisionServiceError(
                {"template_key": "Choose a recognised decision template."}
            )

    decision = Decision(
        organisation=workspace.organisation,
        workspace=workspace,
        title=title,
        decision_question=decision_question,
        purpose=purpose,
        context=context,
        scope=scope,
        contribution_guidance=contribution_guidance,
        urgency=urgency,
        target_decision_date=target_decision_date,
        contribution_deadline=contribution_deadline,
        source_template_key=selected_template.key if selected_template else "",
        source_template_version=selected_template.version if selected_template else None,
        source_method_version=selected_method_version,
        owner=owner,
        created_by=actor,
    )
    decision.full_clean(validate_unique=False, validate_constraints=False)
    decision.save()

    from apps.participants.services import ensure_owner_participant

    ensure_owner_participant(decision=decision, owner=owner, actor=actor)
    if selected_method_version is not None:
        from apps.methodology.models import DecisionMethodUsage

        usage = DecisionMethodUsage(
            organisation=decision.organisation, method_version=selected_method_version,
            decision=decision, applied_by=actor,
        )
        usage.full_clean(validate_unique=False, validate_constraints=False)
        usage.save()
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
            "template_key": decision.source_template_key,
            "template_version": decision.source_template_version,
            "method_version_id": str(decision.source_method_version_id) if decision.source_method_version_id else None,
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
    from apps.participants.models import Participant

    recipients = User.objects.filter(
        decision_participations__decision=decision,
        decision_participations__status=Participant.Status.ACTIVE,
    ).distinct()
    notify_users(
        recipients=recipients,
        exclude_user_id=actor.id,
        organisation=decision.organisation,
        decision=decision,
        kind=Notification.Kind.LIFECYCLE,
        title=f"Decision moved to {Decision.Status(to_status).label}",
        message=(
            f"“{decision.title}” moved from "
            f"{Decision.Status(from_status).label} to "
            f"{Decision.Status(to_status).label}."
        ),
        url=f"/decisions/{decision.id}",
        dedup_key_prefix=f"decision-transition:{transition_record.id}",
        metadata={"from_status": from_status, "to_status": to_status},
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
