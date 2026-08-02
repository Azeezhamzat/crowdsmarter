import pytest
from django.core.exceptions import ValidationError

from apps.decisions.models import DecisionTransition


@pytest.mark.django_db
def test_transition_history_is_immutable(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory()
    transition = DecisionTransition.objects.create(
        decision=decision,
        organisation=decision.organisation,
        sequence=1,
        from_status="draft",
        to_status="framing",
        actor=decision.owner,
    )

    transition.rationale = "Changed later"
    with pytest.raises(ValidationError, match="immutable"):
        transition.save()
    with pytest.raises(ValidationError, match="immutable"):
        DecisionTransition.objects.filter(id=transition.id).delete()
