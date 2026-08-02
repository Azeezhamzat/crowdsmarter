"""Tenant-safe option selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.decisions.models import Decision
from apps.decisions.selectors import decision_for_user

from .models import DecisionOption


def options_for_decision(*, user: User, decision_id: UUID) -> models.QuerySet[DecisionOption]:
    """Return options only after resolving a tenant-visible decision."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return DecisionOption.objects.filter(decision=decision).select_related(
        "proposed_by",
        "created_by",
        "withdrawn_by",
    )


def option_for_user(*, user: User, option_id: UUID) -> DecisionOption:
    """Return one option only when its decision is visible to the user."""
    return get_object_or_404(
        DecisionOption.objects.select_related(
            "decision__organisation",
            "proposed_by",
            "created_by",
            "withdrawn_by",
        ).filter(decision__in=Decision.objects.for_user(user)),
        id=option_id,
    )
