"""Transactional lesson capture and archival workflows."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.decisions.models import Decision
from apps.decisions.policies import can_transition_decision
from apps.decisions.services import append_transition_record

from .models import Lesson


class LessonServiceError(ValidationError):
    """Expected lessons-learned workflow failure."""


def _can_curate(*, actor: User, decision: Decision) -> bool:
    return can_transition_decision(actor=actor, decision=decision)


@transaction.atomic
def create_lesson(*, actor: User, decision: Decision, **fields: Any) -> Lesson:
    current = (
        Decision.objects.select_for_update()
        .select_related("organisation", "owner")
        .get(id=decision.id)
    )
    if not _can_curate(actor=actor, decision=current):
        raise PermissionDenied("You cannot curate lessons for this decision.")
    if current.status != Decision.Status.LESSONS_LEARNED:
        raise LessonServiceError("Lessons can be added only after the outcome review is complete.")
    lesson = Lesson(
        organisation=current.organisation,
        decision=current,
        created_by=actor,
        **fields,
    )
    lesson.full_clean(validate_unique=False, validate_constraints=False)
    lesson.save()
    record_event(
        action="lesson.created",
        object_type="lesson",
        object_id=str(lesson.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.id),
            "category": lesson.category,
            "title": lesson.title,
        },
    )
    return lesson


@transaction.atomic
def update_lesson(*, actor: User, lesson: Lesson, fields: dict[str, Any]) -> Lesson:
    current = (
        Lesson.objects.select_for_update()
        .select_related("decision", "organisation", "decision__owner")
        .get(id=lesson.id)
    )
    if not _can_curate(actor=actor, decision=current.decision):
        raise PermissionDenied("You cannot edit this lesson.")
    if current.decision.status != Decision.Status.LESSONS_LEARNED:
        raise LessonServiceError("Archived decision lessons are read-only.")
    if current.status != Lesson.Status.ACTIVE:
        raise LessonServiceError("Retired lessons are read-only.")
    before = {field: getattr(current, field) for field in fields}
    for field, value in fields.items():
        setattr(current, field, value)
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=[*fields, "updated_at"])
    record_event(
        action="lesson.updated",
        object_type="lesson",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={
            "decision_id": str(current.decision_id),
            "before": before,
            "after": {field: getattr(current, field) for field in fields},
        },
    )
    return current


@transaction.atomic
def retire_lesson(*, actor: User, lesson: Lesson) -> Lesson:
    current = (
        Lesson.objects.select_for_update()
        .select_related("decision", "organisation", "decision__owner")
        .get(id=lesson.id)
    )
    if not _can_curate(actor=actor, decision=current.decision):
        raise PermissionDenied("You cannot retire this lesson.")
    if current.decision.status != Decision.Status.LESSONS_LEARNED:
        raise LessonServiceError("Archived decision lessons are read-only.")
    current.status = Lesson.Status.RETIRED
    current.retired_by = actor
    current.full_clean(validate_unique=False, validate_constraints=False)
    current.save(update_fields=["status", "retired_by", "updated_at"])
    record_event(
        action="lesson.retired",
        object_type="lesson",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"decision_id": str(current.decision_id)},
    )
    return current


@transaction.atomic
def archive_decision(
    *, actor: User, decision: Decision, expected_status: str, rationale: str
) -> None:
    current = (
        Decision.objects.select_for_update()
        .select_related("organisation", "owner")
        .get(id=decision.id)
    )
    if not _can_curate(actor=actor, decision=current):
        raise PermissionDenied("You do not hold lifecycle authority for this decision.")
    if current.status != expected_status:
        raise LessonServiceError(
            {
                "expected_status": (
                    "The decision changed after this page was loaded. Refresh and retry."
                )
            }
        )
    if current.status != Decision.Status.LESSONS_LEARNED:
        raise LessonServiceError("Only a lessons-learned decision may be archived.")
    if not rationale.strip():
        raise LessonServiceError({"rationale": "Record why the learning cycle is complete."})
    if not Lesson.objects.filter(
        decision=current,
        status=Lesson.Status.ACTIVE,
    ).exists():
        raise LessonServiceError(
            {"lessons": "Capture at least one active lesson before archiving."}
        )
    append_transition_record(
        decision=current,
        actor=actor,
        to_status=Decision.Status.ARCHIVED,
        rationale=rationale,
    )
    record_event(
        action="decision.archived_after_learning",
        object_type="decision",
        object_id=str(current.id),
        actor=actor,
        organisation=current.organisation,
        metadata={"rationale": rationale.strip()},
    )
