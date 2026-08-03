from datetime import timedelta

import pytest
from django.utils import timezone

from apps.decisions.models import Decision
from apps.foresight.mapping_services import create_canvas, create_driver
from apps.foresight.models import ForesightCanvas, Signal
from apps.foresight.scenario_services import (
    create_scenario_set,
    create_signpost,
    create_signpost_observation,
)
from apps.notifications.models import Notification
from apps.notifications.services import (
    create_notification,
    deliver_due_review_notifications,
    deliver_signpost_watchlist_notifications,
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


def _build_signpost(*, organisation, actor, decision, review_cadence="quarterly"):  # type: ignore[no-untyped-def]
    canvas = create_canvas(
        actor=actor,
        organisation=organisation,
        title="Watchlist notification canvas",
        focal_question="What could force a revisit?",
        scope="A bounded system for notification testing.",
        horizon_year=2035,
        status=ForesightCanvas.Status.ACTIVE,
    )
    axis_x = create_driver(
        actor=actor, canvas=canvas, title="Axis X", description="Moves either way.",
        driver_type="critical_uncertainty", steep_category=Signal.SteepCategory.ECONOMIC,
        impact=5, uncertainty=5,
    )
    axis_y = create_driver(
        actor=actor, canvas=canvas, title="Axis Y", description="Moves either way.",
        driver_type="critical_uncertainty", steep_category=Signal.SteepCategory.SOCIAL,
        impact=5, uncertainty=5,
    )
    scenario_set = create_scenario_set(
        actor=actor, canvas=canvas, title="Notification scenario set",
        purpose="Exercise watchlist notifications.",
        axis_x_driver_id=axis_x.id, axis_x_low_label="Low", axis_x_high_label="High",
        axis_y_driver_id=axis_y.id, axis_y_low_label="Low", axis_y_high_label="High",
        linked_decision_id=decision.id,
    )
    return create_signpost(
        actor=actor, scenario_set=scenario_set, title="Notification signpost",
        description="Tracks whether the plan should be revisited.",
        indicator="A concrete observable indicator", threshold="Exceeds the agreed trigger",
        direction="above", review_cadence=review_cadence, scenario_links=[],
    )


@pytest.mark.django_db
def test_signpost_watchlist_notifies_on_strong_observation(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        status=Decision.Status.UNDER_REVIEW,
    )
    signpost = _build_signpost(organisation=organisation, actor=actor, decision=decision)
    create_signpost_observation(
        actor=actor,
        signpost=signpost,
        observed_on=timezone.localdate().isoformat(),
        value="Well past the threshold.",
        assessment="strong",
        evidence="Independent data confirms the movement.",
    )

    assert deliver_signpost_watchlist_notifications() == 1
    assert deliver_signpost_watchlist_notifications() == 0
    assert (
        Notification.objects.filter(kind=Notification.Kind.SIGNPOST_WATCH).count() == 1
    )


@pytest.mark.django_db
def test_signpost_watchlist_notifies_when_overdue(
    organisation_factory, decision_factory
):  # type: ignore[no-untyped-def]
    organisation = organisation_factory()
    actor = organisation.created_by
    decision = decision_factory(
        workspace=organisation.workspaces.get(is_default=True),
        owner=actor,
        status=Decision.Status.UNDER_REVIEW,
    )
    signpost = _build_signpost(
        organisation=organisation, actor=actor, decision=decision, review_cadence="monthly"
    )

    assert deliver_signpost_watchlist_notifications(
        on_date=timezone.localdate() + timedelta(days=45)
    ) == 1
    assert deliver_signpost_watchlist_notifications(
        on_date=timezone.localdate() + timedelta(days=45)
    ) == 0
    assert deliver_signpost_watchlist_notifications(
        on_date=timezone.localdate() + timedelta(days=10)
    ) == 0
