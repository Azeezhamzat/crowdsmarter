import pytest

from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.risks.models import Risk
from apps.risks.services import create_risk, update_risk


@pytest.mark.django_db
def test_owner_records_and_closes_risk(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    risk = create_risk(
        actor=decision.owner,
        decision=decision,
        title="Farmer consent is delayed",
        description="Consent may not be completed before the planned pilot start.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MITIGATE,
        mitigation_plan="Prepare plain-language consent materials and start engagement early.",
    )

    update_risk(actor=decision.owner, risk=risk, fields={"status": Risk.Status.CLOSED})
    risk.refresh_from_db()

    assert risk.status == Risk.Status.CLOSED
    assert AuditEvent.objects.filter(object_id=str(risk.id)).count() == 2
