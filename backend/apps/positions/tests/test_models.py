import pytest
from django.core.exceptions import ValidationError

from apps.decision_options.services import create_option
from apps.decisions.models import Decision
from apps.positions.models import Position
from apps.positions.services import submit_position


@pytest.mark.django_db
def test_support_position_requires_decision_option(
    decision_factory,
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)

    with pytest.raises(ValidationError) as exc_info:
        submit_position(
            actor=decision.owner,
            decision=decision,
            recommendation=Position.Recommendation.SUPPORT,
            rationale="The option is proportionate.",
            confidence=Position.Confidence.MEDIUM,
        )

    assert "preferred_option" in exc_info.value.message_dict


@pytest.mark.django_db
def test_submitted_position_is_immutable(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.UNDER_REVIEW)
    option = create_option(
        actor=decision.owner,
        decision=decision,
        title="Run a pilot",
        description="Test the approach on a limited scale.",
    )
    position = submit_position(
        actor=decision.owner,
        decision=decision,
        preferred_option_id=option.id,
        recommendation=Position.Recommendation.SUPPORT,
        rationale="A pilot preserves learning while limiting exposure.",
        confidence=Position.Confidence.HIGH,
    )

    position.rationale = "Changed later"
    with pytest.raises(ValidationError, match="immutable"):
        position.save()
    with pytest.raises(ValidationError, match="immutable"):
        Position.objects.filter(id=position.id).update(rationale="Changed")
