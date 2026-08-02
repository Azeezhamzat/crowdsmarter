import pytest
from django.core.exceptions import ValidationError

from apps.decisions.models import Decision
from apps.lessons.models import Lesson


@pytest.mark.django_db
def test_lesson_rejects_cross_tenant_decision(decision_factory):  # type: ignore[no-untyped-def]
    first = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    second = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    lesson = Lesson(
        organisation=first.organisation,
        decision=second,
        title="Cross tenant",
        insight="Should fail.",
        category=Lesson.Category.OTHER,
        applicability="Nowhere.",
        created_by=first.owner,
    )
    with pytest.raises(ValidationError) as exc_info:
        lesson.full_clean(validate_unique=False, validate_constraints=False)
    assert "organisation" in exc_info.value.message_dict
