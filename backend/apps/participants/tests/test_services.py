import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.participants.services import (
    ParticipantServiceError,
    add_participant,
    change_participant_role,
    remove_participant,
)


@pytest.mark.django_db
def test_owner_adds_changes_and_removes_participant(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )

    participant = add_participant(
        actor=decision.owner,
        decision=decision,
        user=stakeholder,
        role=Participant.Role.CONTRIBUTOR,
    )
    changed = change_participant_role(
        actor=decision.owner,
        participant=participant,
        role=Participant.Role.REVIEWER,
    )
    removed = remove_participant(actor=decision.owner, participant=changed)

    assert removed.status == Participant.Status.REMOVED
    assert removed.removed_at is not None
    assert AuditEvent.objects.filter(
        organisation=decision.organisation,
        action="participant.removed",
        object_id=str(participant.id),
    ).exists()


@pytest.mark.django_db
def test_non_member_cannot_be_participant(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    outsider = user_factory()

    with pytest.raises(ParticipantServiceError, match="active members"):
        add_participant(
            actor=decision.owner,
            decision=decision,
            user=outsider,
            role=Participant.Role.OBSERVER,
        )


@pytest.mark.django_db
def test_decision_owner_participant_cannot_be_removed(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    owner_participant = Participant.objects.get(
        decision=decision,
        role=Participant.Role.DECISION_OWNER,
    )

    with pytest.raises(ParticipantServiceError, match="owner cannot be removed"):
        remove_participant(actor=decision.owner, participant=owner_participant)


@pytest.mark.django_db
def test_participants_cannot_be_changed_after_under_review(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )

    with pytest.raises(PermissionDenied, match="current state"):
        add_participant(
            actor=decision.owner,
            decision=decision,
            user=stakeholder,
            role=Participant.Role.REVIEWER,
        )


@pytest.mark.django_db
def test_removed_participant_can_be_restored_without_losing_history(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    stakeholder = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=stakeholder,
        role=Membership.Role.CONTRIBUTOR,
    )
    participant = add_participant(
        actor=decision.owner,
        decision=decision,
        user=stakeholder,
        role=Participant.Role.OBSERVER,
    )
    removed = remove_participant(actor=decision.owner, participant=participant)

    restored = add_participant(
        actor=decision.owner,
        decision=decision,
        user=stakeholder,
        role=Participant.Role.REVIEWER,
    )

    assert restored.id == removed.id
    assert restored.status == Participant.Status.ACTIVE
    assert restored.role == Participant.Role.REVIEWER
    assert restored.removed_at is None
    assert restored.removed_by is None
