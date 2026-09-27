from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.decisions.models import Decision
from apps.reviews.models import DecisionReview


@pytest.mark.django_db
def test_review_requires_active_tenant_owner(user_factory, decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.DECISION_FINALISED)
    outsider = user_factory()
    review = DecisionReview(
        organisation=decision.organisation,
        decision=decision,
        implementation_owner=outsider,
        commitment_statement="Proceed.",
        success_measures="Measure the result.",
        review_due_date=timezone.localdate() + timedelta(days=30),
        commitment_rationale="Approved.",
        commitment_recorded_by=decision.owner,
    )
    with pytest.raises(ValidationError) as exc_info:
        review.full_clean(validate_unique=False, validate_constraints=False)
    assert "implementation_owner" in exc_info.value.message_dict
