"""Transactional immutable stakeholder position submissions."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.decisions.models import Decision
from apps.participants.models import Participant

from .models import Position
from .policies import active_position_participant, can_submit_position


class PositionServiceError(ValidationError):
    """Expected position workflow failure."""


def _preferred_option(
    *, decision: Decision, option_id: Any | None
) -> DecisionOption | None:
    if option_id is None:
        return None
    try:
        return DecisionOption.objects.get(
            id=option_id,
            decision=decision,
            status=DecisionOption.Status.ACTIVE,
        )
    except DecisionOption.DoesNotExist as exc:
        raise PositionServiceError(
            {"preferred_option_id": "Select an active option from this decision."}
        ) from exc


@transaction.atomic
def submit_position(
    *,
    actor: User,
    decision: Decision,
    preferred_option_id: Any | None = None,
    **fields: Any,
) -> Position:
    """Append a new immutable version of the actor's recommendation."""
    decision = Decision.objects.select_for_update().select_related("organisation").get(
        id=decision.id
    )
    if not can_submit_position(actor=actor, decision=decision):
        raise PermissionDenied(
            "You must be an active non-observer participant to submit a position."
        )
    participant = active_position_participant(actor=actor, decision=decision)
    if participant is None:
        raise PermissionDenied("No eligible participant record was found.")
    participant = Participant.objects.select_for_update().get(id=participant.id)
    current_version = (
        Position.objects.filter(decision=decision, participant=participant).aggregate(
            maximum=Max("version")
        )["maximum"]
        or 0
    )
    position = Position(
        organisation=decision.organisation,
        decision=decision,
        participant=participant,
        participant_role=participant.role,
        preferred_option=_preferred_option(
            decision=decision,
            option_id=preferred_option_id,
        ),
        version=current_version + 1,
        submitted_by=actor,
        **fields,
    )
    position.full_clean(validate_unique=False, validate_constraints=False)
    position.save()
    record_event(
        action="position.submitted",
        object_type="position",
        object_id=str(position.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "participant_id": str(participant.id),
            "version": position.version,
            "recommendation": position.recommendation,
            "preferred_option_id": (
                str(position.preferred_option_id)
                if position.preferred_option_id
                else None
            ),
        },
    )
    return position
