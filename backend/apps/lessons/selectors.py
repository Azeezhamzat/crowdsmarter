"""Tenant-safe lesson selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.selectors import decision_for_user

from .models import Lesson


def lessons_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Lesson]:
    decision = decision_for_user(user=user, decision_id=decision_id)
    return Lesson.objects.filter(decision=decision).select_related("created_by", "retired_by")


def lesson_for_user(*, user: User, lesson_id: UUID) -> Lesson:
    return get_object_or_404(
        Lesson.objects.select_related("decision", "organisation", "created_by").filter(
            decision__organisation__memberships__user=user,
            decision__organisation__memberships__status="active",
        ),
        id=lesson_id,
    )
