"""Explicit notification delivery services."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any
from uuid import UUID

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.organisations.models import Organisation

from .models import Notification


def create_notification(
    *,
    recipient: User,
    organisation: Organisation,
    kind: str,
    title: str,
    message: str,
    decision: Decision | None = None,
    url: str = "",
    metadata: dict[str, Any] | None = None,
    dedup_key: str = "",
) -> Notification:
    """Create one notification, returning an existing deduplicated item when needed."""
    values = {
        "recipient": recipient,
        "organisation": organisation,
        "decision": decision,
        "kind": kind,
        "title": title,
        "message": message,
        "url": url,
        "metadata": metadata or {},
        "dedup_key": dedup_key,
    }
    notification = Notification(**values)
    notification.full_clean(validate_unique=False, validate_constraints=False)
    try:
        with transaction.atomic():
            notification.save()
    except IntegrityError:
        if not dedup_key:
            raise
        return Notification.objects.get(recipient=recipient, dedup_key=dedup_key)
    return notification


def notify_users(
    *,
    recipients: Iterable[User],
    organisation: Organisation,
    kind: str,
    title: str,
    message: str,
    decision: Decision | None = None,
    url: str = "",
    metadata: dict[str, Any] | None = None,
    dedup_key_prefix: str = "",
    exclude_user_id: UUID | None = None,
) -> list[Notification]:
    """Deliver the same workflow message to distinct recipients."""
    created: list[Notification] = []
    seen: set[str] = set()
    for recipient in recipients:
        recipient_id = str(recipient.id)
        if recipient_id in seen or recipient.id == exclude_user_id:
            continue
        seen.add(recipient_id)
        dedup_key = (
            f"{dedup_key_prefix}:{recipient_id}" if dedup_key_prefix else ""
        )
        created.append(
            create_notification(
                recipient=recipient,
                organisation=organisation,
                decision=decision,
                kind=kind,
                title=title,
                message=message,
                url=url,
                metadata=metadata,
                dedup_key=dedup_key,
            )
        )
    return created


@transaction.atomic
def mark_notification_read(*, notification: Notification) -> Notification:
    current = Notification.objects.select_for_update().get(id=notification.id)
    if current.read_at is None:
        current.read_at = timezone.now()
        current.save(update_fields=["read_at", "updated_at"])
    return current


@transaction.atomic
def mark_all_notifications_read(*, recipient: User) -> int:
    return Notification.objects.filter(recipient=recipient, read_at__isnull=True).update(
        read_at=timezone.now(),
        updated_at=timezone.now(),
    )


def deliver_due_review_notifications(*, on_date: date | None = None) -> int:
    """Notify accountable owners once when an outcome review becomes due."""
    from apps.reviews.models import DecisionReview

    due_date = on_date or timezone.localdate()
    reviews = DecisionReview.objects.filter(
        reviewed_at__isnull=True,
        review_due_date__lte=due_date,
    ).select_related("implementation_owner", "organisation", "decision")
    delivered = 0
    for review in reviews:
        before = Notification.objects.filter(
            recipient=review.implementation_owner,
            dedup_key=f"outcome-review-due:{review.id}",
        ).exists()
        create_notification(
            recipient=review.implementation_owner,
            organisation=review.organisation,
            decision=review.decision,
            kind=Notification.Kind.REVIEW_DUE,
            title="Outcome review is due",
            message=(
                f"The outcome review for “{review.decision.title}” was due on "
                f"{review.review_due_date.isoformat()}."
            ),
            url=f"/decisions/{review.decision_id}/outcomes",
            dedup_key=f"outcome-review-due:{review.id}",
            metadata={"review_due_date": review.review_due_date.isoformat()},
        )
        if not before:
            delivered += 1
    return delivered
