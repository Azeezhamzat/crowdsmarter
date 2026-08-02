"""Transactional risk workflows."""

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
from apps.notifications.models import Notification
from apps.notifications.services import create_notification

from .models import Risk


class RiskServiceError(ValidationError):
    """Expected risk workflow failure."""


def _option(*, decision: Decision, option_id: Any | None) -> DecisionOption | None:
    if option_id is None:
        return None
    try:
        return DecisionOption.objects.get(id=option_id, decision=decision)
    except DecisionOption.DoesNotExist as exc:
        raise RiskServiceError(
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
        raise RiskServiceError(
            {"owner_id": "The owner must be an active organisation member."}
        ) from exc


@transaction.atomic
def create_risk(
    *,
    actor: User,
    decision: Decision,
    option_id: Any | None = None,
    owner_id: Any | None = None,
    **fields: Any,
) -> Risk:
    if not can_contribute_reasoning(actor=actor, decision=decision):
        raise PermissionDenied("You cannot add risks in this decision state.")
    risk = Risk(
        organisation=decision.organisation,
        decision=decision,
        option=_option(decision=decision, option_id=option_id),
        owner=_owner(decision=decision, owner_id=owner_id, actor=actor),
        created_by=actor,
        **fields,
    )
    risk.full_clean(validate_unique=False, validate_constraints=False)
    risk.save()
    if risk.owner_id != actor.id:
        create_notification(
            recipient=risk.owner,
            organisation=decision.organisation,
            decision=decision,
            kind=Notification.Kind.ASSIGNMENT,
            title="You own a decision risk",
            message=f"You were assigned the risk “{risk.title}” in “{decision.title}”.",
            url=f"/decisions/{decision.id}/reasoning/risks",
            dedup_key=f"risk-owner:{risk.id}:{risk.owner_id}",
        )
    record_event(
        action="risk.created", object_type="risk", object_id=str(risk.id),
        actor=actor, organisation=decision.organisation,
        metadata={"decision_id": str(decision.id), "title": risk.title, "score": risk.score},
    )
    return risk


@transaction.atomic
def update_risk(*, actor: User, risk: Risk, fields: dict[str, Any]) -> Risk:
    risk = (
        Risk.objects.select_for_update()
        .select_related("decision__organisation")
        .get(id=risk.id)
    )
    if not can_edit_reasoning(
        actor=actor,
        decision=risk.decision,
        created_by_id=risk.created_by_id,
        accountable_user_id=risk.owner_id,
    ):
        raise PermissionDenied("You cannot edit this risk in the current decision state.")
    previous_owner_id = risk.owner_id
    before = {field: getattr(risk, field) for field in fields}
    if "option_id" in fields:
        risk.option = _option(decision=risk.decision, option_id=fields.pop("option_id"))
    if "owner_id" in fields:
        risk.owner = _owner(
            decision=risk.decision,
            owner_id=fields.pop("owner_id"),
            actor=actor,
        )
    for field, value in fields.items():
        setattr(risk, field, value)
    risk.full_clean(validate_unique=False, validate_constraints=False)
    risk.save()
    if risk.owner_id != previous_owner_id and risk.owner_id != actor.id:
        create_notification(
            recipient=risk.owner,
            organisation=risk.organisation,
            decision=risk.decision,
            kind=Notification.Kind.ASSIGNMENT,
            title="You now own a decision risk",
            message=f"You were assigned the risk “{risk.title}” in “{risk.decision.title}”.",
            url=f"/decisions/{risk.decision_id}/reasoning/risks",
            dedup_key=f"risk-owner:{risk.id}:{risk.owner_id}",
        )
    after = {field: getattr(risk, field) for field in before}
    record_event(
        action="risk.updated", object_type="risk", object_id=str(risk.id),
        actor=actor, organisation=risk.organisation,
        metadata={"decision_id": str(risk.decision_id), "before": before, "after": after},
    )
    return risk
