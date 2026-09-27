"""Transactional evidence workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.decisions.reasoning_policies import can_contribute_reasoning, can_edit_reasoning
from apps.foresight.models import Source

from .models import Evidence


class EvidenceServiceError(ValidationError):
    """Expected evidence workflow failure."""


def _option(*, decision: Decision, option_id: Any | None) -> DecisionOption | None:
    if option_id is None:
        return None
    try:
        return DecisionOption.objects.get(
            id=option_id,
            decision=decision,
            organisation=decision.organisation,
        )
    except DecisionOption.DoesNotExist as exc:
        raise EvidenceServiceError(
            {"option_id": "The option does not belong to this decision."}
        ) from exc


def _source(*, decision: Decision, source_id: Any | None) -> Source | None:
    if source_id is None:
        return None
    try:
        return Source.objects.get(id=source_id, organisation=decision.organisation)
    except Source.DoesNotExist as exc:
        raise EvidenceServiceError(
            {"source_id": "The source does not belong to this organisation."}
        ) from exc


@transaction.atomic
def create_evidence(
    *,
    actor: User,
    decision: Decision,
    option_id: Any | None = None,
    source_id: Any | None = None,
    **fields: Any,
) -> Evidence:
    if not can_contribute_reasoning(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add evidence in this decision state.")
    item = Evidence(
        organisation=decision.organisation,
        decision=decision,
        option=_option(decision=decision, option_id=option_id),
        source=_source(decision=decision, source_id=source_id),
        created_by=actor,
        **fields,
    )
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    record_event(
        action="evidence.created",
        object_type="evidence",
        object_id=str(item.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "title": item.title},
    )
    return item


@transaction.atomic
def update_evidence(
    *,
    actor: User,
    item: Evidence,
    fields: dict[str, Any],
) -> Evidence:
    item = (
        Evidence.objects.select_for_update()
        .select_related("decision__organisation")
        .get(id=item.id)
    )
    if not can_edit_reasoning(
        actor=actor, decision=item.decision, created_by_id=item.created_by_id
    ):
        raise PermissionDenied("You cannot edit this evidence in the current decision state.")
    before = {field: getattr(item, field) for field in fields}
    if "option_id" in fields:
        item.option = _option(decision=item.decision, option_id=fields.pop("option_id"))
    if "source_id" in fields:
        item.source = _source(decision=item.decision, source_id=fields.pop("source_id"))
    requested_status = fields.pop("status", None)
    for field, value in fields.items():
        setattr(item, field, value)
    if requested_status is not None:
        item.mark_status(status=requested_status, actor=actor)
    item.full_clean(validate_unique=False, validate_constraints=False)
    item.save()
    after = {field: getattr(item, field) for field in before}
    record_event(
        action="evidence.updated",
        object_type="evidence",
        object_id=str(item.id),
        actor=actor,
        organisation=item.organisation,
        metadata={"decision_id": str(item.decision_id), "before": before, "after": after},
    )
    return item
