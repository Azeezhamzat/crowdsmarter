"""Explicit decision collaboration workflows."""

from __future__ import annotations

from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.notifications.services import notify_users
from apps.organisations.models import Membership

from .models import DiscussionEntry
from .policies import can_contribute, can_resolve


class CollaborationServiceError(ValidationError):
    """Raised when a collaboration command violates a business rule."""


def _mentioned_users(*, decision: Decision, user_ids: list[UUID]) -> list[User]:
    unique_ids = list(dict.fromkeys(user_ids))
    if len(unique_ids) > 20:
        raise CollaborationServiceError("A discussion entry may mention at most 20 people.")
    users = list(
        User.objects.filter(
            id__in=unique_ids,
            organisation_memberships__organisation=decision.organisation,
            organisation_memberships__status=Membership.Status.ACTIVE,
        ).distinct()
    )
    if len(users) != len(unique_ids):
        raise CollaborationServiceError(
            "Every mentioned person must be an active organisation member."
        )
    return users


@transaction.atomic
def create_discussion_entry(
    *,
    actor: User,
    decision: Decision,
    kind: str,
    body: str,
    mentioned_user_ids: list[UUID] | None = None,
    reply_to: DiscussionEntry | None = None,
) -> DiscussionEntry:
    """Append one attributable discussion entry and deliver focused notifications."""
    current = Decision.objects.select_for_update().select_related(
        "organisation", "owner"
    ).get(id=decision.id)
    if not can_contribute(actor=actor, decision=current):
        raise PermissionDenied(
            "Only an active non-observer participant or organisation manager may contribute."
        )
    if reply_to and reply_to.decision_id != current.id:
        raise CollaborationServiceError("A reply must belong to the same decision.")

    mentions = _mentioned_users(
        decision=current,
        user_ids=mentioned_user_ids or [],
    )
    entry = DiscussionEntry(
        organisation=current.organisation,
        decision=current,
        author=actor,
        kind=kind,
        body=body,
        reply_to=reply_to,
    )
    entry.full_clean(validate_unique=False, validate_constraints=False)
    entry.save()
    if mentions:
        entry.mentioned_users.set(mentions)

    recipients: list[User] = list(mentions)
    if reply_to and reply_to.author_id != actor.id:
        recipients.append(reply_to.author)
    if kind in {DiscussionEntry.Kind.QUESTION, DiscussionEntry.Kind.CONCERN}:
        recipients.append(current.owner)
    notify_users(
        recipients=recipients,
        organisation=current.organisation,
        decision=current,
        kind=Notification.Kind.COLLABORATION,
        title=f"New {entry.get_kind_display().lower()} on a decision",
        message=f"{actor.email} added a {entry.get_kind_display().lower()} to “{current.title}”.",
        url=f"/decisions/{current.id}/collaboration",
        metadata={"discussion_entry_id": str(entry.id), "kind": entry.kind},
        dedup_key_prefix=f"discussion-entry:{entry.id}",
        exclude_user_id=actor.id,
    )
    record_event(
        action="collaboration.entry_created",
        object_type="discussion_entry",
        object_id=str(entry.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "kind": entry.kind,
            "reply_to_id": str(reply_to.id) if reply_to else None,
            "mentioned_user_ids": [str(user.id) for user in mentions],
        },
    )
    return entry


@transaction.atomic
def resolve_discussion_entry(
    *, actor: User, entry: DiscussionEntry, resolution_note: str
) -> DiscussionEntry:
    """Resolve an open question or concern without changing its original content."""
    current = DiscussionEntry.objects.select_for_update().select_related(
        "decision", "decision__organisation", "author"
    ).get(id=entry.id)
    if not can_resolve(actor=actor, entry=current):
        raise PermissionDenied(
            "Only the decision owner or an organisation manager may resolve this item."
        )
    if current.kind not in {
        DiscussionEntry.Kind.QUESTION,
        DiscussionEntry.Kind.CONCERN,
    }:
        raise CollaborationServiceError("Only questions and concerns can be resolved.")
    if current.is_resolved:
        raise CollaborationServiceError("This discussion item is already resolved.")

    current.resolved_at = timezone.now()
    current.resolved_by = actor
    current.resolution_note = resolution_note
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(
        update_fields=["resolved_at", "resolved_by", "resolution_note", "updated_at"]
    )
    notify_users(
        recipients=[current.author],
        organisation=current.organisation,
        decision=current.decision,
        kind=Notification.Kind.COLLABORATION,
        title=f"{current.get_kind_display()} resolved",
        message=(
            f"A {current.get_kind_display().lower()} on "
            f"“{current.decision.title}” was resolved."
        ),
        url=f"/decisions/{current.decision_id}/collaboration",
        metadata={"discussion_entry_id": str(current.id)},
        dedup_key_prefix=f"discussion-resolved:{current.id}",
        exclude_user_id=actor.id,
    )
    record_event(
        action="collaboration.entry_resolved",
        object_type="discussion_entry",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.decision_id),
            "kind": current.kind,
            "resolution_note": current.resolution_note,
        },
    )
    return current
