"""Tenant-safe assumption selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.decisions.selectors import decision_for_user

from .models import Assumption


def assumptions_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Assumption]:
    """Return assumptions only after resolving a tenant-visible decision."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return Assumption.objects.filter(decision=decision).select_related(
        "option",
        "owner",
        "created_by",
    )


def assumption_for_user(*, user: User, assumption_id: UUID) -> Assumption:
    """Return one assumption only when its decision is visible."""
    return get_object_or_404(
        Assumption.objects.select_related(
            "decision__organisation",
            "option",
            "owner",
            "created_by",
        ).filter(decision__in=Decision.objects.for_user(user)),
        id=assumption_id,
    )
