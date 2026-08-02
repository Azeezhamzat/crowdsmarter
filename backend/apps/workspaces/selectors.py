"""Tenant-safe read selectors for workspaces."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.organisations.selectors import organisation_for_user

from .models import Workspace


def workspaces_for_organisation(
    *, user: User, organisation_id: UUID
) -> models.QuerySet[Workspace]:
    """List workspaces only after establishing organisation access."""
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return Workspace.objects.filter(organisation=organisation).select_related(
        "organisation", "created_by"
    )


def workspace_for_user(*, user: User, workspace_id: UUID) -> Workspace:
    """Fetch a workspace without revealing another tenant's records."""
    return get_object_or_404(
        Workspace.objects.for_user(user).select_related("organisation", "created_by"),
        id=workspace_id,
    )
