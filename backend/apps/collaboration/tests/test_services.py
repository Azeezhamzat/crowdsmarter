import pytest
from django.core.exceptions import PermissionDenied, ValidationError

from apps.audit.models import AuditEvent
from apps.collaboration.models import DiscussionEntry
from apps.collaboration.services import create_discussion_entry, resolve_discussion_entry
from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.organisations.models import Membership
from apps.participants.models import Participant


@pytest.mark.django_db
def test_participant_adds_attributable_question_and_mentions_member(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    contributor = user_factory()
    mentioned = user_factory()
    for user in (contributor, mentioned):
        Membership.objects.create(
            organisation=decision.organisation,
            user=user,
            role=Membership.Role.CONTRIBUTOR,
        )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=contributor,
        role=Participant.Role.CONTRIBUTOR,
        added_by=decision.owner,
    )

    entry = create_discussion_entry(
        actor=contributor,
        decision=decision,
        kind=DiscussionEntry.Kind.QUESTION,
        body="Which evidence will validate the field baseline?",
        mentioned_user_ids=[mentioned.id],
    )

    assert list(entry.mentioned_users.values_list("id", flat=True)) == [mentioned.id]
    assert Notification.objects.filter(
        recipient=mentioned,
        kind=Notification.Kind.COLLABORATION,
    ).exists()
    assert AuditEvent.objects.filter(
        action="collaboration.entry_created",
        object_id=str(entry.id),
    ).exists()


@pytest.mark.django_db
def test_observer_cannot_contribute(decision_factory, user_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    observer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=observer,
        role=Membership.Role.VIEWER,
    )
    Participant.objects.create(
        organisation=decision.organisation,
        decision=decision,
        user=observer,
        role=Participant.Role.OBSERVER,
        added_by=decision.owner,
    )

    with pytest.raises(PermissionDenied, match="non-observer"):
        create_discussion_entry(
            actor=observer,
            decision=decision,
            kind=DiscussionEntry.Kind.NOTE,
            body="This should not be accepted.",
        )


@pytest.mark.django_db
def test_owner_resolves_concern_without_rewriting_original(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    entry = create_discussion_entry(
        actor=decision.owner,
        decision=decision,
        kind=DiscussionEntry.Kind.CONCERN,
        body="The implementation owner is not yet named.",
    )
    resolved = resolve_discussion_entry(
        actor=decision.owner,
        entry=entry,
        resolution_note="The owner will be named in the commitment record.",
    )
    assert resolved.is_resolved
    assert resolved.body == "The implementation owner is not yet named."

    resolved.body = "Changed content"
    with pytest.raises(ValidationError, match="immutable"):
        resolved.save()


@pytest.mark.django_db
def test_archived_decision_discussion_is_read_only(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.ARCHIVED)
    with pytest.raises(PermissionDenied):
        create_discussion_entry(
            actor=decision.owner,
            decision=decision,
            kind=DiscussionEntry.Kind.UPDATE,
            body="A late update.",
        )
