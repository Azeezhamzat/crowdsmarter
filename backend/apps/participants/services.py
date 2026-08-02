"""Transactional participant workflows."""

from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.policies import can_manage_participants
from apps.organisations.models import Membership, Organisation

from .models import Participant


class ParticipantServiceError(ValidationError):
    """Expected validation failure in a participant workflow."""


ASSIGNABLE_ROLES = {
    Participant.Role.DECISION_MAKER,
    Participant.Role.CONTRIBUTOR,
    Participant.Role.REVIEWER,
    Participant.Role.OBSERVER,
}


def _require_active_member(*, decision: Decision, user: User) -> None:
    if not Membership.objects.filter(
        organisation=decision.organisation,
        user=user,
        status=Membership.Status.ACTIVE,
    ).exists():
        raise ParticipantServiceError(
            {"email": "Participants must be active members of the organisation."}
        )


def _require_manager(*, actor: User, decision: Decision) -> None:
    if not can_manage_participants(actor=actor, decision=decision):
        raise PermissionDenied("You cannot manage participants in this decision state.")


@transaction.atomic
def ensure_owner_participant(*, decision: Decision, owner: User, actor: User) -> Participant:
    """Create the system-managed participant representation of decision ownership."""
    _require_active_member(decision=decision, user=owner)
    participant = Participant(
        organisation=decision.organisation,
        decision=decision,
        user=owner,
        role=Participant.Role.DECISION_OWNER,
        status=Participant.Status.ACTIVE,
        added_by=actor,
    )
    participant.full_clean(validate_unique=False, validate_constraints=False)
    participant.save()
    record_event(
        action="participant.created",
        object_type="participant",
        object_id=str(participant.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "user_id": str(owner.id),
            "role": Participant.Role.DECISION_OWNER,
            "system_managed": True,
        },
    )
    return participant


@transaction.atomic
def change_owner_participant(*, decision: Decision, owner: User, actor: User) -> Participant:
    """Synchronise participant ownership after an explicit decision transfer."""
    _require_active_member(decision=decision, user=owner)
    current = Participant.objects.select_for_update().get(
        decision=decision,
        status=Participant.Status.ACTIVE,
        role=Participant.Role.DECISION_OWNER,
    )
    if current.user_id == owner.id:
        return current
    previous_owner_id = current.user_id
    current.role = Participant.Role.CONTRIBUTOR
    current.save(update_fields=["role", "updated_at"])
    participant, created = Participant.objects.get_or_create(
        decision=decision,
        user=owner,
        status=Participant.Status.ACTIVE,
        defaults={
            "organisation": decision.organisation,
            "role": Participant.Role.DECISION_OWNER,
            "added_by": actor,
        },
    )
    if not created:
        participant.role = Participant.Role.DECISION_OWNER
        participant.save(update_fields=["role", "updated_at"])
    record_event(
        action="participant.owner_changed",
        object_type="participant",
        object_id=str(participant.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "previous_owner_id": str(previous_owner_id),
            "owner_id": str(owner.id),
        },
    )
    return participant


@transaction.atomic
def add_participant(
    *, actor: User, decision: Decision, user: User, role: str
) -> Participant:
    """Add or restore an organisation member as a decision participant."""
    decision = Decision.objects.select_for_update().select_related("organisation").get(
        id=decision.id
    )
    _require_manager(actor=actor, decision=decision)
    if role not in ASSIGNABLE_ROLES:
        raise ParticipantServiceError({"role": "That participant role cannot be assigned."})
    _require_active_member(decision=decision, user=user)
    if Participant.objects.filter(
        decision=decision,
        user=user,
        status=Participant.Status.ACTIVE,
    ).exists():
        raise ParticipantServiceError("That user already participates in this decision.")

    removed = Participant.objects.filter(
        decision=decision,
        user=user,
        status=Participant.Status.REMOVED,
    ).order_by("-updated_at").first()
    if removed:
        removed.role = role
        removed.status = Participant.Status.ACTIVE
        removed.removed_at = None
        removed.removed_by = None
        removed.added_by = actor
        removed.full_clean(validate_unique=False, validate_constraints=False)
        removed.save(
            update_fields=[
                "role",
                "status",
                "removed_at",
                "removed_by",
                "added_by",
                "updated_at",
            ]
        )
        participant = removed
    else:
        participant = Participant(
            organisation=decision.organisation,
            decision=decision,
            user=user,
            role=role,
            added_by=actor,
        )
        participant.full_clean(validate_unique=False, validate_constraints=False)
        try:
            participant.save()
        except IntegrityError as exc:
            raise ParticipantServiceError(
                "That user already participates in this decision."
            ) from exc
    record_event(
        action="participant.created",
        object_type="participant",
        object_id=str(participant.id),
        actor=actor,
        organisation=decision.organisation,
        metadata={
            "decision_id": str(decision.id),
            "user_id": str(user.id),
            "role": role,
            "system_managed": False,
        },
    )
    return participant


@transaction.atomic
def change_participant_role(
    *, actor: User, participant: Participant, role: str
) -> Participant:
    """Change a stakeholder role without modifying decision ownership."""
    participant = Participant.objects.select_for_update().select_related(
        "decision", "decision__organisation", "user"
    ).get(id=participant.id, status=Participant.Status.ACTIVE)
    _require_manager(actor=actor, decision=participant.decision)
    if participant.role == Participant.Role.DECISION_OWNER:
        raise ParticipantServiceError(
            "Transfer decision ownership through the decision framing record."
        )
    if role not in ASSIGNABLE_ROLES:
        raise ParticipantServiceError({"role": "That participant role cannot be assigned."})
    previous_role = participant.role
    participant.role = role
    participant.full_clean(validate_unique=False, validate_constraints=False)
    participant.save(update_fields=["role", "updated_at"])
    record_event(
        action="participant.role_changed",
        object_type="participant",
        object_id=str(participant.id),
        actor=actor,
        organisation=participant.organisation,
        metadata={
            "decision_id": str(participant.decision_id),
            "user_id": str(participant.user_id),
            "previous_role": previous_role,
            "role": role,
        },
    )
    return participant


@transaction.atomic
def remove_participant(*, actor: User, participant: Participant) -> Participant:
    """Soft-remove a stakeholder while preserving participation history."""
    participant = Participant.objects.select_for_update().select_related(
        "decision", "decision__organisation", "user"
    ).get(id=participant.id, status=Participant.Status.ACTIVE)
    _require_manager(actor=actor, decision=participant.decision)
    if participant.role == Participant.Role.DECISION_OWNER:
        raise ParticipantServiceError("The decision owner cannot be removed as a participant.")
    participant.status = Participant.Status.REMOVED
    participant.removed_at = timezone.now()
    participant.removed_by = actor
    participant.full_clean(validate_unique=False, validate_constraints=False)
    participant.save(
        update_fields=["status", "removed_at", "removed_by", "updated_at"]
    )
    record_event(
        action="participant.removed",
        object_type="participant",
        object_id=str(participant.id),
        actor=actor,
        organisation=participant.organisation,
        metadata={
            "decision_id": str(participant.decision_id),
            "user_id": str(participant.user_id),
            "role": participant.role,
        },
    )
    return participant


@transaction.atomic
def remove_non_owner_participations_for_member_departure(
    *,
    actor: User,
    organisation: Organisation,
    user: User,
) -> int:
    """Close ordinary assignments when a human leaves a tenant.

    Decision ownership is handled separately because it requires an explicit
    transfer. Other assignments are soft-removed so offboarding can revoke
    tenant access immediately without erasing organisational history.
    """
    participants = list(
        Participant.objects.select_for_update()
        .select_related("decision")
        .filter(
            organisation=organisation,
            user=user,
            status=Participant.Status.ACTIVE,
        )
        .exclude(role=Participant.Role.DECISION_OWNER)
    )
    removed_at = timezone.now()
    for participant in participants:
        participant.status = Participant.Status.REMOVED
        participant.removed_at = removed_at
        participant.removed_by = actor
        participant.full_clean(validate_unique=False, validate_constraints=False)
        participant.save(
            update_fields=["status", "removed_at", "removed_by", "updated_at"]
        )
        record_event(
            action="participant.removed",
            object_type="participant",
            object_id=str(participant.id),
            actor=actor,
            organisation=organisation,
            metadata={
                "decision_id": str(participant.decision_id),
                "user_id": str(user.id),
                "role": participant.role,
                "reason": "membership_removed",
            },
        )
    return len(participants)
