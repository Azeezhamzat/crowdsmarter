"""Transactional human decision finalisation workflow."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decision_options.models import DecisionOption
from apps.participants.models import Participant
from apps.positions.models import Position
from apps.positions.selectors import current_positions_queryset

from .models import Decision, DecisionFinalisation
from .policies import has_finalisation_authority
from .services import append_transition_record


class DecisionFinalisationError(ValidationError):
    """Expected failure in a human finalisation command."""


def _selected_option(*, decision: Decision, option_id: Any) -> DecisionOption:
    try:
        return DecisionOption.objects.get(
            id=option_id,
            decision=decision,
            status=DecisionOption.Status.ACTIVE,
        )
    except DecisionOption.DoesNotExist as exc:
        raise DecisionFinalisationError(
            {"selected_option_id": "Select an active option from this decision."}
        ) from exc


def _position_snapshot(*, decision: Decision) -> tuple[list[dict[str, Any]], list[Position]]:
    current_positions = list(current_positions_queryset(decision=decision))
    snapshot = [
        {
            "position_id": str(position.id),
            "participant_id": str(position.participant_id),
            "user_id": str(position.participant.user_id),
            "email": position.participant.user.email,
            "participant_role": position.participant_role,
            "version": position.version,
            "recommendation": position.recommendation,
            "preferred_option_id": (
                str(position.preferred_option_id)
                if position.preferred_option_id
                else None
            ),
            "confidence": position.confidence,
            "rationale": position.rationale,
            "conditions": position.conditions,
            "submitted_at": position.created_at.isoformat(),
        }
        for position in current_positions
    ]
    return snapshot, current_positions


def _validate_authority_positions(
    *, decision: Decision, current_positions: list[Position]
) -> None:
    required = list(
        Participant.objects.filter(
            decision=decision,
            status=Participant.Status.ACTIVE,
            role__in=[
                Participant.Role.DECISION_OWNER,
                Participant.Role.DECISION_MAKER,
            ],
        ).select_related("user")
    )
    if not required:
        raise DecisionFinalisationError(
            {"positions": "At least one active human decision authority is required."}
        )
    positioned_ids = {position.participant_id for position in current_positions}
    missing = [
        participant.user.email
        for participant in required
        if participant.id not in positioned_ids
    ]
    if missing:
        raise DecisionFinalisationError(
            {
                "positions": (
                    "Each active decision authority must submit a current position. "
                    f"Missing: {', '.join(missing)}."
                )
            }
        )


def _has_dissent(*, positions: list[Position], selected_option: DecisionOption) -> bool:
    supporting = {
        Position.Recommendation.SUPPORT,
        Position.Recommendation.SUPPORT_WITH_CONDITIONS,
    }
    return any(
        position.recommendation not in supporting
        or position.preferred_option_id != selected_option.id
        for position in positions
    )


@transaction.atomic
def finalise_decision(
    *,
    actor: User,
    decision: Decision,
    expected_status: str,
    selected_option_id: Any,
    rationale: str,
    conditions: str = "",
    dissent_summary: str = "",
    positions_reviewed: bool,
) -> DecisionFinalisation:
    """Select an option and create the immutable human final decision record."""
    decision = Decision.objects.select_for_update().select_related(
        "organisation",
        "owner",
    ).get(id=decision.id)
    if not has_finalisation_authority(actor=actor, decision=decision):
        raise PermissionDenied("You do not hold authority to finalise this decision.")
    if decision.status != expected_status:
        raise DecisionFinalisationError(
            {
                "expected_status": (
                    "The decision changed after this page was loaded. Refresh and retry."
                )
            }
        )
    if decision.status != Decision.Status.READY_FOR_DECISION:
        raise DecisionFinalisationError(
            "Only a decision in Ready for Decision may be finalised."
        )
    if DecisionFinalisation.objects.filter(decision=decision).exists():
        raise DecisionFinalisationError("This decision already has a finalisation record.")
    if not positions_reviewed:
        raise DecisionFinalisationError(
            {"positions_reviewed": "Confirm that the current stakeholder positions were reviewed."}
        )
    selected_option = _selected_option(
        decision=decision,
        option_id=selected_option_id,
    )
    snapshot, current_positions = _position_snapshot(decision=decision)
    _validate_authority_positions(
        decision=decision,
        current_positions=current_positions,
    )
    if _has_dissent(positions=current_positions, selected_option=selected_option):
        if not dissent_summary.strip():
            raise DecisionFinalisationError(
                {
                    "dissent_summary": (
                        "Record how dissenting or alternative positions were considered."
                    )
                }
            )
    finalisation = DecisionFinalisation(
        organisation=decision.organisation,
        decision=decision,
        selected_option=selected_option,
        decided_by=actor,
        rationale=rationale,
        conditions=conditions,
        dissent_summary=dissent_summary,
        position_snapshot=snapshot,
    )
    finalisation.full_clean(validate_unique=False, validate_constraints=False)
    finalisation.save()
    append_transition_record(
        decision=decision,
        actor=actor,
        to_status=Decision.Status.DECISION_FINALISED,
        rationale=finalisation.rationale,
        warnings_acknowledged=(
            ["Stakeholder dissent was reviewed and recorded."]
            if finalisation.dissent_summary
            else []
        ),
    )
    record_event(
        action="decision.finalised",
        object_type="decision_finalisation",
        object_id=str(finalisation.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "selected_option_id": str(selected_option.id),
            "selected_option_title": selected_option.title,
            "position_count": len(snapshot),
            "dissent_recorded": bool(finalisation.dissent_summary),
        },
    )
    return finalisation
