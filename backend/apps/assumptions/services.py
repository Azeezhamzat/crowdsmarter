"""Transactional assumption workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
from apps.organisations.models import Membership

from .models import Assumption


class AssumptionServiceError(ValidationError):
    """Expected assumption workflow failure."""


def _option(*, decision: Decision, option_id: Any | None) -> DecisionOption | None:
    if option_id is None:
        return None
    try:
        return DecisionOption.objects.get(id=option_id, decision=decision)
    except DecisionOption.DoesNotExist as exc:
        raise AssumptionServiceError(
            {"option_id": "The option does not belong to this decision."}
        ) from exc


def _owner(*, decision: Decision, owner_id: Any | None, actor: User) -> User:
    if owner_id is None:
        return actor
    try:
        return Membership.objects.select_related("user").get(
            organisation=decision.organisation,
            user_id=owner_id,
            status=Membership.Status.ACTIVE,
        ).user
    except Membership.DoesNotExist as exc:
        raise AssumptionServiceError(
            {"owner_id": "The owner must be an active organisation member."}
        ) from exc


@transaction.atomic
def create_assumption(
    *,
    actor: User,
    decision: Decision,
    option_id: Any | None = None,
    owner_id: Any | None = None,
    **fields: Any,
) -> Assumption:
    if not can_contribute_reasoning(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add assumptions in this decision state.")
    assumption = Assumption(
        organisation=decision.organisation,
        decision=decision,
        option=_option(decision=decision, option_id=option_id),
        owner=_owner(decision=decision, owner_id=owner_id, actor=actor),
        created_by=actor,
        **fields,
    )
    assumption.full_clean(validate_unique=False, validate_constraints=False)
    assumption.save()
    record_event(
        action="assumption.created",
        object_type="assumption",
        object_id=str(assumption.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "statement": assumption.statement[:240]},
    )
    return assumption


@transaction.atomic
def update_assumption(
    *, actor: User, assumption: Assumption, fields: dict[str, Any]
) -> Assumption:
    assumption = Assumption.objects.select_for_update().select_related(
        "decision__organisation"
    ).get(id=assumption.id)
    if not can_edit_reasoning(
        actor=actor,
        decision=assumption.decision,
        created_by_id=assumption.created_by_id,
        accountable_user_id=assumption.owner_id,
    ):
        raise PermissionDenied("You cannot edit this assumption in the current decision state.")
    before = {field: getattr(assumption, field) for field in fields}
    if "option_id" in fields:
        assumption.option = _option(
            decision=assumption.decision, option_id=fields.pop("option_id")
        )
    if "owner_id" in fields:
        assumption.owner = _owner(
            decision=assumption.decision,
            owner_id=fields.pop("owner_id"),
            actor=actor,
        )
    for field, value in fields.items():
        setattr(assumption, field, value)
    assumption.full_clean(validate_unique=False, validate_constraints=False)
    assumption.save()
    after = {field: getattr(assumption, field) for field in before}
    record_event(
        action="assumption.updated",
        object_type="assumption",
        object_id=str(assumption.id),
        actor=actor,
        organisation=assumption.organisation,
        metadata={"decision_id": str(assumption.decision_id), "before": before, "after": after},
    )
    return assumption
