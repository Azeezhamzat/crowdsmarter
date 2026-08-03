import pytest
from django.core.exceptions import ValidationError

from apps.criteria.models import Criterion


@pytest.mark.django_db
def test_must_have_criterion_requires_threshold(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    criterion = Criterion(
        organisation=decision.organisation,
        decision=decision,
        title="Regulatory compliance",
        description="The option must satisfy the relevant regulatory regime.",
        direction=Criterion.Direction.MAXIMIZE,
        weight=40,
        is_must_have=True,
        owner=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        criterion.full_clean()


@pytest.mark.django_db
def test_criterion_belongs_to_decision_organisation(
    decision_factory, organisation_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    other_organisation = organisation_factory()
    criterion = Criterion(
        organisation=other_organisation,
        decision=decision,
        title="Cost",
        description="Total cost of ownership over three years.",
        direction=Criterion.Direction.MINIMIZE,
        weight=30,
        owner=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        criterion.full_clean()
