import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decision_options.services import create_option
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import ConflictOfInterest, Participant
from apps.participants.services import (
    ParticipantServiceError,
    add_participant,
    change_participant_role,
    conflicts_for_decision,
    declare_conflict,
    remove_participant,
    withdraw_conflict,
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

    with pytest.raises(PermissionDenied, match="decision state"):
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


def _reviewer_participant(decision, user_factory):  # type: ignore[no-untyped-def]
    reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation, user=reviewer, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )
    return Participant.objects.create(
        organisation=decision.organisation, decision=decision, user=reviewer,
        role=Participant.Role.REVIEWER, added_by=decision.owner,
    )


@pytest.mark.django_db
def test_reviewer_self_declares_option_conflict(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    participant = _reviewer_participant(decision, user_factory)

    conflict = declare_conflict(
        actor=participant.user, participant=participant,
        scope=ConflictOfInterest.Scope.OPTION, option=option, reason="I fund this org.",
    )

    assert conflict.scope == ConflictOfInterest.Scope.OPTION
    assert conflict.option == option
    assert conflict.withdrawn_at is None
    assert AuditEvent.objects.filter(action="conflict_of_interest.declared").exists()


@pytest.mark.django_db
def test_other_reviewer_cannot_declare_on_behalf(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    participant = _reviewer_participant(decision, user_factory)
    other_reviewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation, user=other_reviewer, role=Membership.Role.CONTRIBUTOR,
        status=Membership.Status.ACTIVE,
    )

    with pytest.raises(PermissionDenied):
        declare_conflict(
            actor=other_reviewer, participant=participant, scope=ConflictOfInterest.Scope.DECISION,
        )


@pytest.mark.django_db
def test_manager_can_declare_on_behalf_of_reviewer(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    participant = _reviewer_participant(decision, user_factory)

    conflict = declare_conflict(
        actor=decision.owner, participant=participant, scope=ConflictOfInterest.Scope.DECISION,
        reason="Family relationship with the round sponsor.",
    )

    assert conflict.scope == ConflictOfInterest.Scope.DECISION
    assert conflict.option is None


@pytest.mark.django_db
def test_option_scope_requires_option(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    participant = _reviewer_participant(decision, user_factory)

    with pytest.raises(ParticipantServiceError, match="requires an option"):
        declare_conflict(
            actor=participant.user, participant=participant, scope=ConflictOfInterest.Scope.OPTION,
        )


@pytest.mark.django_db
def test_reviewer_withdraws_own_conflict(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    participant = _reviewer_participant(decision, user_factory)
    conflict = declare_conflict(
        actor=participant.user, participant=participant,
        scope=ConflictOfInterest.Scope.OPTION, option=option,
    )

    withdrawn = withdraw_conflict(actor=participant.user, conflict=conflict)

    assert withdrawn.withdrawn_at is not None
    assert withdrawn.withdrawn_by == participant.user
    assert conflicts_for_decision(decision=decision).count() == 0


@pytest.mark.django_db
def test_duplicate_active_option_conflict_is_rejected(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    option = create_option(actor=decision.owner, decision=decision, title="App", description="Desc.")
    participant = _reviewer_participant(decision, user_factory)
    declare_conflict(
        actor=participant.user, participant=participant,
        scope=ConflictOfInterest.Scope.OPTION, option=option,
    )

    with pytest.raises(ParticipantServiceError, match="already covers"):
        declare_conflict(
            actor=participant.user, participant=participant,
            scope=ConflictOfInterest.Scope.OPTION, option=option,
        )
