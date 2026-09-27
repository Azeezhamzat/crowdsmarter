"""Tenant-safe decision selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.workspaces.selectors import workspace_for_user

from .models import Decision, DecisionTransition


def decisions_for_workspace(*, user: User, workspace_id: UUID) -> models.QuerySet[Decision]:
    """List decisions only after establishing workspace access."""
    workspace = workspace_for_user(user=user, workspace_id=workspace_id)
    return Decision.objects.filter(workspace=workspace).select_related(
        "organisation", "workspace", "owner", "created_by"
    )


def decision_for_user(*, user: User, decision_id: UUID) -> Decision:
    """Fetch a decision without cross-tenant existence disclosure."""
    return get_object_or_404(
        Decision.objects.for_user(user).select_related(
            "organisation", "workspace", "owner", "created_by"
        ),
        id=decision_id,
    )


def transitions_for_decision(
    *, user: User, decision_id: UUID
) -> models.QuerySet[DecisionTransition]:
    """Return immutable lifecycle history after tenant access is established."""
    decision = decision_for_user(user=user, decision_id=decision_id)
    return DecisionTransition.objects.filter(decision=decision).select_related("actor")
