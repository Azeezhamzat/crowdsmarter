import pytest
from django.core.exceptions import ValidationError

from apps.decision_options.models import DecisionOption


@pytest.mark.django_db
def test_option_rejects_cross_tenant_decision(
    decision_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    other = organisation_factory()
    option = DecisionOption(
        organisation=other,
        decision=decision,
        title="Cross-tenant option",
        description="This must never validate.",
        proposed_by=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        option.full_clean()


@pytest.mark.django_db
def test_withdrawn_option_requires_metadata(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    option = DecisionOption(
        organisation=decision.organisation,
        decision=decision,
        title="Withdrawn without metadata",
        description="Invalid soft-state transition.",
        status=DecisionOption.Status.WITHDRAWN,
        proposed_by=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError, match="withdrawal timestamp"):
        option.full_clean()


@pytest.mark.django_db
def test_experiment_option_requires_notes(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    option = DecisionOption(
        organisation=decision.organisation,
        decision=decision,
        title="Small pilot",
        description="Test the approach in one region first.",
        is_experiment=True,
        proposed_by=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError, match="bounded experiment"):
        option.full_clean()
