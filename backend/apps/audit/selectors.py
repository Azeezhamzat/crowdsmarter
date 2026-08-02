"""Tenant-safe audit event selectors."""

from __future__ import annotations

from uuid import UUID

from django.core.exceptions import PermissionDenied
from django.db import models

from apps.accounts.models import User
from apps.organisations.models import Membership
from apps.organisations.selectors import organisation_for_user

from .models import AuditEvent


def audit_events_for_organisation(
    *,
    user: User,
    organisation_id: UUID,
    action: str = "",
    object_type: str = "",
) -> models.QuerySet[AuditEvent]:
    """Return audit events only to active organisation managers."""
    organisation = organisation_for_user(
        user=user,
        organisation_id=organisation_id,
    )
    membership = organisation.memberships.filter(
        user=user,
        status=Membership.Status.ACTIVE,
    ).first()
    if membership is None or membership.role not in {
        Membership.Role.OWNER,
        Membership.Role.ADMIN,
    }:
        raise PermissionDenied("Only organisation managers may read the audit log.")
    queryset = AuditEvent.objects.filter(organisation=organisation).select_related("actor")
    if action:
        queryset = queryset.filter(action=action)
    if object_type:
        queryset = queryset.filter(object_type=object_type)
    return queryset
