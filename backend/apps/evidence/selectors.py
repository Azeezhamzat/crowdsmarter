"""Tenant-safe evidence selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.decisions.selectors import decision_for_user

from .models import Evidence


def evidence_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Evidence]:
    """Return evidence only after resolving a tenant-visible decision."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return Evidence.objects.filter(decision=decision).select_related(
        "option",
        "created_by",
        "withdrawn_by",
    )


def evidence_for_user(*, user: User, evidence_id: UUID) -> Evidence:
    """Return one evidence record only when its decision is visible."""
    return get_object_or_404(
        Evidence.objects.select_related(
            "decision__organisation",
            "option",
            "created_by",
            "withdrawn_by",
        ).filter(decision__in=Decision.objects.for_user(user)),
        id=evidence_id,
    )
