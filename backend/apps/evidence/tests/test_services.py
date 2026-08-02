import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.evidence.models import Evidence
from apps.evidence.services import create_evidence, update_evidence
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_owner_creates_and_withdraws_evidence(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    item = create_evidence(
        actor=decision.owner,
        decision=decision,
        title="Pilot detection results",
        summary="The pilot detected relevant incidents two days earlier on average.",
        source_type=Evidence.SourceType.INTERNAL_DATA,
        source_reference="Pilot monitoring dataset v1",
        stance=Evidence.Stance.SUPPORTS,
        strength=Evidence.Strength.MODERATE,
    )

    update_evidence(
        actor=decision.owner,
        item=item,
        fields={"status": Evidence.Status.WITHDRAWN},
    )
    item.refresh_from_db()

    assert item.withdrawn_at is not None
    assert AuditEvent.objects.filter(object_id=str(item.id)).count() == 2


@pytest.mark.django_db
def test_viewer_cannot_add_evidence(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.OPEN_FOR_CONTRIBUTION)
    viewer = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=viewer,
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(PermissionDenied):
        create_evidence(
            actor=viewer,
            decision=decision,
            title="Not permitted",
            summary="View-only members cannot add evidence.",
            source_type=Evidence.SourceType.OTHER,
            source_reference="None",
            stance=Evidence.Stance.CONTEXT,
        )
