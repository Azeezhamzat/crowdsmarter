"""Explicit notification delivery services."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
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
        dedup_key = f"{dedup_key_prefix}:{recipient_id}" if dedup_key_prefix else ""
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


_SIGNPOST_CADENCE_DAYS = {
    "monthly": 30,
    "quarterly": 90,
    "semiannual": 182,
    "annual": 365,
}


def deliver_signpost_watchlist_notifications(*, on_date: date | None = None) -> int:
    """Notify accountable people when a signpost moves sharply or falls overdue for review."""
    from apps.foresight.models import Signpost, SignpostObservation

    due_date = on_date or timezone.localdate()
    delivered = 0

    strong_observations = (
        SignpostObservation.objects.filter(
            assessment__in=[
                SignpostObservation.Assessment.STRONG,
                SignpostObservation.Assessment.CONTRADICTORY,
            ],
        )
        .select_related(
            "signpost__owner",
            "signpost__scenario_set__linked_decision__owner",
            "signpost__scenario_set__canvas__organisation",
        )
        .prefetch_related(
            "signpost__assumption_links__assumption__owner",
            "signpost__risk_links__risk__owner",
        )
    )
    for observation in strong_observations:
        signpost = observation.signpost
        organisation = signpost.scenario_set.canvas.organisation
        recipients = {signpost.owner}
        linked_decision = signpost.scenario_set.linked_decision
        if linked_decision is not None:
            recipients.add(linked_decision.owner)
        for assumption_link in signpost.assumption_links.all():
            recipients.add(assumption_link.assumption.owner)
        for risk_link in signpost.risk_links.all():
            recipients.add(risk_link.risk.owner)
        message = (
            f"“{signpost.title}” recorded {observation.get_assessment_display().lower()} "
            f"on {observation.observed_on.isoformat()}: {observation.value}"
        )
        url = f"/foresight/scenario-sets/{signpost.scenario_set_id}"
        for recipient in recipients:
            dedup_key = f"signpost-observation:{observation.id}:{recipient.id}"
            before = Notification.objects.filter(recipient=recipient, dedup_key=dedup_key).exists()
            create_notification(
                recipient=recipient,
                organisation=organisation,
                decision=linked_decision,
                kind=Notification.Kind.SIGNPOST_WATCH,
                title="Signpost moved: revisit linked work",
                message=message,
                url=url,
                dedup_key=dedup_key,
                metadata={
                    "signpost_id": str(signpost.id),
                    "observation_id": str(observation.id),
                    "assessment": observation.assessment,
                },
            )
            if not before:
                delivered += 1

    active_signposts = (
        Signpost.objects.filter(status=Signpost.Status.ACTIVE)
        .exclude(review_cadence=Signpost.Cadence.EVENT_DRIVEN)
        .select_related(
            "owner", "scenario_set__linked_decision", "scenario_set__canvas__organisation"
        )
        .prefetch_related("observations")
    )
    for signpost in active_signposts:
        cadence_days = _SIGNPOST_CADENCE_DAYS.get(signpost.review_cadence)
        if not cadence_days:
            continue
        observations = list(signpost.observations.all())
        anchor = observations[0].observed_on if observations else signpost.created_at.date()
        next_due = anchor + timedelta(days=cadence_days)
        if next_due > due_date:
            continue
        organisation = signpost.scenario_set.canvas.organisation
        dedup_key = f"signpost-overdue:{signpost.id}:{anchor.isoformat()}"
        before = Notification.objects.filter(recipient=signpost.owner, dedup_key=dedup_key).exists()
        create_notification(
            recipient=signpost.owner,
            organisation=organisation,
            decision=signpost.scenario_set.linked_decision,
            kind=Notification.Kind.SIGNPOST_WATCH,
            title="Signpost is due for review",
            message=(
                f"“{signpost.title}” has had no observation recorded since "
                f"{anchor.isoformat()}, past its "
                f"{signpost.get_review_cadence_display().lower()} cadence."
            ),
            url=f"/foresight/scenario-sets/{signpost.scenario_set_id}",
            dedup_key=dedup_key,
            metadata={"signpost_id": str(signpost.id), "anchor_date": anchor.isoformat()},
        )
        if not before:
            delivered += 1

    return delivered
