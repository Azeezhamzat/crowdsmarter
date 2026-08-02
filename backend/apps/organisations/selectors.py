"""Read-side tenant-safe selectors."""

from __future__ import annotations

from uuid import UUID

from django.db import models
from django.shortcuts import get_object_or_404

from apps.accounts.models import User

from .models import Membership, Organisation


def organisations_for_user(user: User) -> models.QuerySet[Organisation]:
    """Return only organisations visible to the user."""
    return Organisation.objects.for_user(user).select_related("created_by")


def organisation_for_user(*, user: User, organisation_id: UUID) -> Organisation:
    """Fetch an organisation without revealing whether another tenant exists."""
    return get_object_or_404(organisations_for_user(user), id=organisation_id)


def memberships_for_user_organisation(
    *, user: User, organisation_id: UUID
) -> models.QuerySet[Membership]:
    """Return memberships only after establishing tenant access."""
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return Membership.objects.filter(organisation=organisation).select_related(
        "user", "organisation"
    )


def membership_for_user(*, user: User, membership_id: UUID) -> Membership:
    """Fetch a membership only when its organisation is visible to the user."""
    return get_object_or_404(
        Membership.objects.select_related("organisation", "user").filter(
            organisation__in=Organisation.objects.for_user(user)
        ),
        id=membership_id,
    )
