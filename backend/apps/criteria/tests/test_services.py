import pytest

from apps.audit.models import AuditEvent
from apps.criteria.models import Criterion
from apps.criteria.services import create_criterion, update_criterion
from apps.decisions.models import Decision


@pytest.mark.django_db
def test_owner_creates_and_retires_a_criterion(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    criterion = create_criterion(
        actor=decision.owner,
        decision=decision,
        title="Community acceptance",
        description="How well the option is received by affected communities.",
        direction=Criterion.Direction.MAXIMIZE,
        weight=25,
    )

    assert criterion.order == 1

    update_criterion(actor=decision.owner, criterion=criterion, fields={"status": Criterion.Status.RETIRED})
    criterion.refresh_from_db()

    assert criterion.status == Criterion.Status.RETIRED
    assert AuditEvent.objects.filter(object_id=str(criterion.id)).count() == 2


@pytest.mark.django_db
def test_criteria_are_ordered_by_creation_when_order_not_given(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    first = create_criterion(
        actor=decision.owner, decision=decision, title="Cost",
        description="Total cost.", direction=Criterion.Direction.MINIMIZE, weight=40,
    )
    second = create_criterion(
        actor=decision.owner, decision=decision, title="Speed",
        description="Time to implement.", direction=Criterion.Direction.MINIMIZE, weight=20,
    )

    assert first.order == 1
    assert second.order == 2
