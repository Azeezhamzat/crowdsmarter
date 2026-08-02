import pytest
from django.core.exceptions import ValidationError

from apps.audit.services import record_event


@pytest.mark.django_db
def test_audit_events_are_append_only(
    user_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    actor = user_factory()
    organisation = organisation_factory(owner=actor)
    event = record_event(
        action="test.recorded",
        object_type="organisation",
        object_id=str(organisation.id),
        actor=actor,
        organisation=organisation,
    )

    event.action = "test.changed"
    with pytest.raises(ValidationError, match="append-only"):
        event.save()
    with pytest.raises(ValidationError, match="append-only"):
        event.delete()
    with pytest.raises(ValidationError, match="append-only"):
        type(event).objects.filter(id=event.id).update(action="test.changed")


@pytest.mark.django_db
def test_audit_actor_cannot_be_hard_deleted(user_factory):  # type: ignore[no-untyped-def]
    from django.db.models.deletion import ProtectedError

    actor = user_factory()
    record_event(
        action="test.recorded",
        object_type="user",
        object_id=str(actor.id),
        actor=actor,
    )

    with pytest.raises(ProtectedError):
        actor.delete()

@pytest.mark.django_db
def test_audit_service_serialises_common_domain_values(
    user_factory,
):  # type: ignore[no-untyped-def]
    from datetime import date
    from decimal import Decimal
    from uuid import uuid4

    from apps.audit.services import record_event

    event = record_event(
        action="test.serialisation",
        object_type="test",
        object_id="1",
        actor=user_factory(),
        metadata={
            "date": date(2026, 7, 26),
            "amount": Decimal("1.25"),
            "identifier": uuid4(),
        },
    )

    assert event.metadata["date"] == "2026-07-26"
    assert event.metadata["amount"] == "1.25"
    assert isinstance(event.metadata["identifier"], str)
