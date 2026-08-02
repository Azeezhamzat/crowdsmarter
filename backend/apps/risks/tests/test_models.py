import pytest
from django.core.exceptions import ValidationError

from apps.risks.models import Risk


@pytest.mark.django_db
def test_risk_score_is_likelihood_times_impact(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    risk = Risk(
        organisation=decision.organisation,
        decision=decision,
        title="Data collection failure",
        description="Field devices may fail to synchronise.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MONITOR,
        owner=decision.owner,
        created_by=decision.owner,
    )

    assert risk.score == 12


@pytest.mark.django_db
def test_mitigation_strategy_requires_plan(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    risk = Risk(
        organisation=decision.organisation,
        decision=decision,
        title="Staff capacity",
        description="Staff may not have sufficient time.",
        likelihood=3,
        impact=4,
        response_strategy=Risk.ResponseStrategy.MITIGATE,
        owner=decision.owner,
        created_by=decision.owner,
    )

    with pytest.raises(ValidationError):
        risk.full_clean()
