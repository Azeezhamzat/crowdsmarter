import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decision_options.services import create_option
from apps.decisions.models import Decision
from apps.organisations.models import Membership
from apps.participants.models import Participant
from apps.participants.services import add_participant, change_participant_role
from apps.positions.models import Position
from apps.positions.services import submit_position


@pytest.mark.django_db
def test_participant_submits_versioned_positions(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    first_option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Pilot",
        description="Run a limited pilot.",
    )
    second_option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Proceed directly",
        description="Begin wider implementation immediately.",
    )

    first = submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=first_option.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="The pilot reduces uncertainty.",
        confidence=Position.Confidence.MEDIUM,
    )
    second = submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=second_option.id,
        recommendation=Position.Recommendation.SUPPORT_WITH_CONDITIONS,
        rationale="New evidence supports faster action.",
        conditions="Review after four weeks.",
        confidence=Position.Confidence.HIGH,
    )

    assert first.version == 1
    assert second.version == 2
    assert Position.objects.filter(decision=decision).count() == 2
    assert AuditEvent.objects.filter(action="position.submitted").count() == 2


@pytest.mark.django_db
def test_observer_cannot_submit_position(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    observer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=observer,
        role=Membership.Role.VIEWER,
    )
    add_participant(
        actor=decision.owner,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
    )

    with pytest.raises(PermissionDenied, match="non-observer"):
        submit_position(
            actor=observer,
            decision=decision,
            recommendation=Position.Recommendation.ABSTAIN,
            rationale="I am observing only.",
            confidence=Position.Confidence.LOW,
        )


@pytest.mark.django_db
def test_position_preserves_participant_role_at_submission(
    user_factory,
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    participant = add_participant(
        actor=decision.owner,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
    )
    position = submit_position(
        actor=contributor,
        decision=decision,
        recommendation=Position.Recommendation.ABSTAIN,
        rationale="More evidence is needed before I can recommend an option.",
        confidence=Position.Confidence.LOW,
    )

    change_participant_role(
        actor=decision.owner,
        participant=participant,
        role=Participant.Role.REVIEWER,
    )
    position.refresh_from_db()
    participant.refresh_from_db()

    assert position.participant_role == Participant.Role.CONTRIBUTOR
    assert participant.role == Participant.Role.REVIEWER
