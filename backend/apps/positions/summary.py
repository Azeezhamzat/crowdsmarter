"""Read-only summaries for stakeholder position coverage."""

from __future__ import annotations

from typing import Any

from apps.participants.models import Participant

from .selectors import current_positions_queryset


def position_summary(decision) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Return current coverage of required human decision authorities."""
    required = list(
        decision.participants.filter(
            status=Participant.Status.ACTIVE,
            role__in=[
                Participant.Role.DECISION_OWNER,
                Participant.Role.DECISION_MAKER,
            ],
        ).select_related("user")
    )
    current_positions = list(current_positions_queryset(decision=decision))
    positioned_participant_ids = {item.participant_id for item in current_positions}
    missing = [
        {
            "participant_id": str(participant.id),
            "email": participant.user.email,
            "role": participant.role,
            "role_label": participant.get_role_display(),
        }
        for participant in required
        if participant.id not in positioned_participant_ids
    ]
    return {
        "current_positions": len(current_positions),
        "required_authorities": len(required),
        "submitted_authorities": len(required) - len(missing),
        "missing_authorities": missing,
        "ready_to_finalise": not missing and bool(required),
    }
