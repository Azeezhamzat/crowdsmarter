import pytest
from django.core.exceptions import PermissionDenied

from apps.audit.models import AuditEvent
from apps.decisions.models import Decision
from apps.lessons.models import Lesson
from apps.lessons.services import LessonServiceError, archive_decision, create_lesson
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_create_lesson_and_archive_learning_cycle(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    lesson = create_lesson(
        actor=decision.owner,
        decision=decision,
        title="Test operational readiness earlier",
        insight="Training needs were underestimated during framing.",
        category=Lesson.Category.IMPLEMENTATION,
        applicability="Future pilots that introduce a new field workflow.",
        recommended_change="Add a staff-readiness check before implementation.",
    )
    archive_decision(
        actor=decision.owner,
        decision=decision,
        expected_status=Decision.Status.LESSONS_LEARNED,
        rationale="The outcome and reusable learning have been recorded.",
    )
    decision.refresh_from_db()
    assert lesson.status == Lesson.Status.ACTIVE
    assert decision.status == Decision.Status.ARCHIVED
    assert AuditEvent.objects.filter(action="decision.archived_after_learning").exists()


@pytest.mark.django_db
def test_archive_requires_active_lesson(decision_factory):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    with pytest.raises(LessonServiceError) as exc_info:
        archive_decision(
            actor=decision.owner,
            decision=decision,
            expected_status=Decision.Status.LESSONS_LEARNED,
            rationale="Attempted closure.",
        )
    assert "lessons" in exc_info.value.message_dict


@pytest.mark.django_db
def test_contributor_cannot_curate_lessons(
    user_factory, decision_factory
):  # type: ignore[no-untyped-def]
    decision = decision_factory(status=Decision.Status.LESSONS_LEARNED)
    contributor = user_factory()
    Membership.objects.create(
        organisation=decision.organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    with pytest.raises(PermissionDenied):
        create_lesson(
            actor=contributor,
            decision=decision,
            title="Unauthorised lesson",
            insight="This should not be created.",
            category=Lesson.Category.OTHER,
            applicability="Nowhere.",
        )
