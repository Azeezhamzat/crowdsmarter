"""Transactional decision option workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
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
    before = {field: getattr(option, field) for field in fields}
    requested_status = fields.pop("status", None)
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
