"""Transactional decision option workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from decimal import Decimal

from django.db.models import Count, Q, Sum

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import (
    can_contribute_reasoning,
    can_edit_reasoning,
    can_manage_option_eligibility,
    can_manage_option_outcome,
)
from apps.organisations.models import Membership

from .models import DecisionOption


class DecisionOptionServiceError(ValidationError):
    """Expected option workflow failure."""


def _active_member(*, decision: Decision, user_id: Any) -> User:
    try:
        return Membership.objects.select_related("user").get(
            organisation=decision.organisation,
            user_id=user_id,
            status=Membership.Status.ACTIVE,
        ).user
    except Membership.DoesNotExist as exc:
        raise DecisionOptionServiceError(
            {"proposed_by_id": "The proposer must be an active organisation member."}
        ) from exc


def _related_options(
    *, decision: Decision, option_id: Any, ids: list[Any], field_name: str
) -> list[DecisionOption]:
    """Resolve related-option ids, rejecting self-reference and cross-decision links."""
    ids = [str(item) for item in ids]
    if str(option_id) in ids:
        raise DecisionOptionServiceError({field_name: "An option cannot reference itself."})
    related = list(DecisionOption.objects.filter(decision=decision, id__in=ids))
    if len(related) != len(set(ids)):
        raise DecisionOptionServiceError(
            {field_name: "Every related option must belong to this decision."}
        )
    return related


@transaction.atomic
def create_option(
    *,
    actor: User,
    decision: Decision,
    title: str,
    description: str,
    expected_benefits: str = "",
    tradeoffs: str = "",
    is_status_quo: bool = False,
    proposed_by_id: Any | None = None,
    estimated_cost: Any | None = None,
    cost_notes: str = "",
    resource_notes: str = "",
    implementation_time_estimate: str = "",
    reversibility: str = "",
    is_experiment: bool = False,
    experiment_notes: str = "",
    depends_on_ids: list[Any] | None = None,
    mutually_exclusive_with_ids: list[Any] | None = None,
) -> DecisionOption:
    if not can_contribute_reasoning(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add options in this decision state.")
    proposer = actor if proposed_by_id is None else _active_member(
        decision=decision, user_id=proposed_by_id
    )
    option = DecisionOption(
        organisation=decision.organisation,
        decision=decision,
        title=title,
        description=description,
        expected_benefits=expected_benefits,
        tradeoffs=tradeoffs,
        is_status_quo=is_status_quo,
        estimated_cost=estimated_cost,
        cost_notes=cost_notes,
        resource_notes=resource_notes,
        implementation_time_estimate=implementation_time_estimate,
        reversibility=reversibility,
        is_experiment=is_experiment,
        experiment_notes=experiment_notes,
        proposed_by=proposer,
        created_by=actor,
    )
    option.full_clean(validate_unique=False, validate_constraints=False)
    try:
        option.save()
    except IntegrityError as exc:
        raise DecisionOptionServiceError(
            {"is_status_quo": "Only one active status quo option is allowed."}
        ) from exc
    if depends_on_ids:
        option.depends_on.set(
            _related_options(
                decision=decision, option_id=option.id, ids=depends_on_ids, field_name="depends_on_ids"
            )
        )
    if mutually_exclusive_with_ids:
        option.mutually_exclusive_with.set(
            _related_options(
                decision=decision,
                option_id=option.id,
                ids=mutually_exclusive_with_ids,
                field_name="mutually_exclusive_with_ids",
            )
        )
    record_event(
        action="decision_option.created",
        object_type="decision_option",
        object_id=str(option.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "title": option.title},
    )
    return option


@transaction.atomic
def update_option(
    *, actor: User, option: DecisionOption, fields: dict[str, Any]
) -> DecisionOption:
    option = DecisionOption.objects.select_for_update().select_related(
        "decision__organisation"
    ).get(id=option.id)
    if not can_edit_reasoning(
        actor=actor,
        decision=option.decision,
        created_by_id=option.created_by_id,
    ):
        raise PermissionDenied("You cannot edit this option in the current decision state.")
    requested_status = fields.pop("status", None)
    depends_on_ids = fields.pop("depends_on_ids", None)
    mutually_exclusive_with_ids = fields.pop("mutually_exclusive_with_ids", None)
    before = {field: getattr(option, field) for field in fields}
    for field, value in fields.items():
        setattr(option, field, value)
    if requested_status is not None:
        option.mark_status(status=requested_status, actor=actor)
    option.full_clean(validate_unique=False, validate_constraints=False)
    try:
        option.save()
    except IntegrityError as exc:
        raise DecisionOptionServiceError(
            {"is_status_quo": "Only one active status quo option is allowed."}
        ) from exc
    if depends_on_ids is not None:
        option.depends_on.set(
            _related_options(
                decision=option.decision,
                option_id=option.id,
                ids=depends_on_ids,
                field_name="depends_on_ids",
            )
        )
    if mutually_exclusive_with_ids is not None:
        option.mutually_exclusive_with.set(
            _related_options(
                decision=option.decision,
                option_id=option.id,
                ids=mutually_exclusive_with_ids,
                field_name="mutually_exclusive_with_ids",
            )
        )
    after = {field: getattr(option, field) for field in before}
    record_event(
        action="decision_option.updated",
        object_type="decision_option",
        object_id=str(option.id),
        actor=actor,
        organisation=option.organisation,
        metadata={"decision_id": str(option.decision_id), "before": before, "after": after},
    )
    return option


@transaction.atomic
def set_eligibility(
    *, actor: User, option: DecisionOption, eligibility_status: str, eligibility_note: str = ""
) -> DecisionOption:
    """Record an eligibility screening decision for an application/option."""
    option = DecisionOption.objects.select_for_update().select_related(
        "decision__organisation"
    ).get(id=option.id)
    if not can_manage_option_eligibility(actor=actor, decision=option.decision):
        raise PermissionDenied("You cannot screen eligibility for this option.")
    before = option.eligibility_status
    option.mark_eligibility(
        eligibility_status=eligibility_status, eligibility_note=eligibility_note, actor=actor
    )
    option.full_clean(validate_unique=False, validate_constraints=False)
    option.save()
    record_event(
        action="decision_option.eligibility_set",
        object_type="decision_option",
        object_id=str(option.id),
        actor=actor,
        organisation=option.organisation,
        metadata={
            "decision_id": str(option.decision_id),
            "before": before,
            "after": eligibility_status,
        },
    )
    return option


@transaction.atomic
def set_outcome(
    *,
    actor: User,
    option: DecisionOption,
    outcome_status: str,
    awarded_amount: Decimal | None = None,
    outcome_note: str = "",
) -> DecisionOption:
    """Record a funding outcome for an application/option, decoupled from finalisation."""
    option = DecisionOption.objects.select_for_update().select_related(
        "decision__organisation"
    ).get(id=option.id)
    if not can_manage_option_outcome(actor=actor, decision=option.decision):
        raise PermissionDenied("You cannot record a funding outcome for this option.")
    before = option.outcome_status
    option.mark_outcome(
        outcome_status=outcome_status,
        awarded_amount=awarded_amount,
        outcome_note=outcome_note,
        actor=actor,
    )
    option.full_clean(validate_unique=False, validate_constraints=False)
    option.save()
    record_event(
        action="decision_option.outcome_set",
        object_type="decision_option",
        object_id=str(option.id),
        actor=actor,
        organisation=option.organisation,
        metadata={
            "decision_id": str(option.decision_id),
            "before": before,
            "after": outcome_status,
        },
    )
    return option


def budget_summary(*, decision: Decision) -> dict[str, Any]:
    """Sum requested vs. awarded amounts and screening/outcome counts for a round."""
    active = DecisionOption.objects.filter(decision=decision, status=DecisionOption.Status.ACTIVE)
    totals = active.aggregate(
        requested_total=Sum("estimated_cost"),
        awarded_total=Sum("awarded_amount", filter=Q(outcome_status=DecisionOption.OutcomeStatus.FUNDED)),
        funded_count=Count("id", filter=Q(outcome_status=DecisionOption.OutcomeStatus.FUNDED)),
        declined_count=Count("id", filter=Q(outcome_status=DecisionOption.OutcomeStatus.DECLINED)),
        pending_outcome_count=Count("id", filter=Q(outcome_status=DecisionOption.OutcomeStatus.PENDING)),
        eligible_count=Count("id", filter=Q(eligibility_status=DecisionOption.EligibilityStatus.ELIGIBLE)),
        ineligible_count=Count("id", filter=Q(eligibility_status=DecisionOption.EligibilityStatus.INELIGIBLE)),
        pending_eligibility_count=Count("id", filter=Q(eligibility_status=DecisionOption.EligibilityStatus.PENDING)),
    )
    return {
        "requested_total": totals["requested_total"] or Decimal("0"),
        "awarded_total": totals["awarded_total"] or Decimal("0"),
        "funded_count": totals["funded_count"],
        "declined_count": totals["declined_count"],
        "pending_outcome_count": totals["pending_outcome_count"],
        "eligible_count": totals["eligible_count"],
        "ineligible_count": totals["ineligible_count"],
        "pending_eligibility_count": totals["pending_eligibility_count"],
    }
