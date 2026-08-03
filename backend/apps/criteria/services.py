"""Transactional decision-criteria workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
from apps.organisations.models import Membership

from .models import Criterion


class CriterionServiceError(ValidationError):
    """Expected criterion workflow failure."""


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
        raise CriterionServiceError(
            {"owner_id": "The owner must be an active organisation member."}
        ) from exc


@transaction.atomic
def create_criterion(
    *,
    actor: User,
    decision: Decision,
    owner_id: Any | None = None,
    **fields: Any,
) -> Criterion:
    if not can_contribute_reasoning(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add criteria in this decision state.")
    if "order" not in fields:
        last_order = (
            Criterion.objects.filter(decision=decision).order_by("-order").values_list(
                "order", flat=True
            ).first()
        )
        fields["order"] = (last_order or 0) + 1
    criterion = Criterion(
        organisation=decision.organisation,
        decision=decision,
        owner=_owner(decision=decision, owner_id=owner_id, actor=actor),
        created_by=actor,
        **fields,
    )
    criterion.full_clean(validate_unique=False, validate_constraints=False)
    criterion.save()
    record_event(
        action="criterion.created", object_type="criterion", object_id=str(criterion.id),
        actor=actor, organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "title": criterion.title, "weight": criterion.weight},
    )
    return criterion


@transaction.atomic
def update_criterion(*, actor: User, criterion: Criterion, fields: dict[str, Any]) -> Criterion:
    criterion = (
        Criterion.objects.select_for_update(of=("self",))
        .select_related("decision__organisation")
        .get(id=criterion.id)
    )
    if not can_edit_reasoning(
        actor=actor,
        decision=criterion.decision,
        created_by_id=criterion.created_by_id,
        accountable_user_id=criterion.owner_id,
    ):
        raise PermissionDenied("You cannot edit this criterion in the current decision state.")
    before = {field: getattr(criterion, field) for field in fields}
    if "owner_id" in fields:
        criterion.owner = _owner(
            decision=criterion.decision,
            owner_id=fields.pop("owner_id"),
            actor=actor,
        )
    for field, value in fields.items():
        setattr(criterion, field, value)
    criterion.full_clean(validate_unique=False, validate_constraints=False)
    criterion.save()
    after = {field: getattr(criterion, field) for field in before}
    record_event(
        action="criterion.updated", object_type="criterion", object_id=str(criterion.id),
        actor=actor, organisation=criterion.organisation,
        metadata={"decision_id": str(criterion.decision_id), "before": before, "after": after},
    )
    return criterion
