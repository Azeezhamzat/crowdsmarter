"""Tenant-safe criterion selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.decisions.selectors import decision_for_user

from .models import Criterion


def criteria_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[Criterion]:
    """Return criteria only after resolving a tenant-visible decision."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return Criterion.objects.filter(decision=decision).select_related("owner", "created_by")


def criterion_for_user(*, user: User, criterion_id: UUID) -> Criterion:
    """Return one criterion only when its decision is visible."""
    return get_object_or_404(
        Criterion.objects.select_related(
            "decision__organisation",
            "owner",
            "created_by",
        ).filter(decision__in=Decision.objects.for_user(user)),
        id=criterion_id,
    )
