import pytest
from django.core.exceptions import ValidationError

from apps.assumptions.models import Assumption
from apps.assumptions.services import create_assumption, update_assumption
from apps.audit.models import AuditEvent
from apps.decisions.models import Decision


@pytest.mark.django_db
def test_owner_records_and_verifies_assumption(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    item = create_assumption(
        actor=decision.owner,
        decision=decision,
        statement="Mobile connectivity will be sufficient for weekly synchronisation.",
        rationale="Coverage maps show service at the pilot sites.",
        impact_if_false="Offline data capture or a different pilot design would be required.",
        confidence=Assumption.Confidence.MEDIUM,
    )

    update_assumption(
        actor=decision.owner,
        assumption=item,
        fields={
            "verification_status": Assumption.VerificationStatus.PARTIALLY_VERIFIED,
            "verification_notes": "Two of three pilot sites were tested successfully.",
        },
    )
    item.refresh_from_db()

    assert item.verification_status == Assumption.VerificationStatus.PARTIALLY_VERIFIED
    assert AuditEvent.objects.filter(object_id=str(item.id)).count() == 2


@pytest.mark.django_db
def test_invalidated_status_without_notes_is_rejected(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    item = create_assumption(
        actor=decision.owner,
        decision=decision,
        statement="The existing devices support the application.",
        impact_if_false="Replacement devices would increase cost.",
        confidence=Assumption.Confidence.LOW,
    )

    with pytest.raises(ValidationError):
        update_assumption(
            actor=decision.owner,
            assumption=item,
            fields={"verification_status": Assumption.VerificationStatus.INVALIDATED},
        )
