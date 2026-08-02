from datetime import timedelta

import pytest
from django.utils import timezone

from apps.decisions.models import Decision
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notification,
    deliver_due_review_notifications,
)
from apps.reviews.models import DecisionReview


@pytest.mark.django_db
def test_notifications_are_deduplicated(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    user = user_factory()
    organisation = organisation_factory(owner=user)
    first = create_notification(
        recipient=user,
        organisation=organisation,
        kind=Notification.Kind.SYSTEM,
        title="One message",
        message="Created once.",
        dedup_key="same-event",
    )
    second = create_notification(
        recipient=user,
        organisation=organisation,
        kind=Notification.Kind.SYSTEM,
        title="One message",
        message="Created once.",
        dedup_key="same-event",
    )
    assert first.id == second.id
    assert Notification.objects.count() == 1


@pytest.mark.django_db
def test_due_review_notification_is_created_once(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.IMPLEMENTATION)
    DecisionReview.objects.create(
        organisation=decision.organisation,
        decision=decision,
        implementation_owner=decision.owner,
        commitment_statement="Deliver the pilot.",
        success_measures="Measure adoption.",
        review_due_date=timezone.localdate() - timedelta(days=1),
        commitment_rationale="Human commitment.",
        commitment_recorded_by=decision.owner,
    )
    assert deliver_due_review_notifications() == 1
    assert deliver_due_review_notifications() == 0
    assert Notification.objects.filter(kind=Notification.Kind.REVIEW_DUE).count() == 1
