import pytest
from django.core.exceptions import ValidationError

from apps.assumptions.models import Assumption


@pytest.mark.django_db
def test_verified_assumption_requires_notes(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    assumption = Assumption(
        organisation=decision.organisation,
        decision=decision,
        statement="Farmers will use the mobile workflow.",
        impact_if_false="Adoption and data quality would be too low.",
        confidence=Assumption.Confidence.MEDIUM,
        verification_status=Assumption.VerificationStatus.VERIFIED,
        owner=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        assumption.full_clean()
