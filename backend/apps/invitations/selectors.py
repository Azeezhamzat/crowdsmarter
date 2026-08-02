"""Tenant-safe invitation queries."""

from __future__ import annotations

from django.db.models import QuerySet

from apps.accounts.models import User

from .models import OrganisationInvitation
from .tokens import digest_token


def invitations_for_manager(
    *,
    user: User,
    organisation_id: str,
) -> QuerySet[OrganisationInvitation]:
    """Return invitations only when the caller manages the organisation."""
    return OrganisationInvitation.objects.filter(
        organisation_id=organisation_id,
        organisation__memberships__user=user,
        organisation__memberships__status="active",
        organisation__memberships__role__in=["owner", "admin"],
    ).select_related("organisation", "invited_by", "accepted_by")


def invitation_for_manager(
    *,
    user: User,
    invitation_id: str,
) -> OrganisationInvitation:
    """Return one manager-visible invitation without cross-tenant disclosure."""
    return OrganisationInvitation.objects.select_related(
        "organisation", "invited_by", "accepted_by"
    ).get(
        id=invitation_id,
        organisation__memberships__user=user,
        organisation__memberships__status="active",
        organisation__memberships__role__in=["owner", "admin"],
    )


def invitation_by_token(*, raw_token: str) -> OrganisationInvitation:
    """Resolve an invitation from its raw secret."""
    return OrganisationInvitation.objects.select_related(
        "organisation", "invited_by", "accepted_by"
    ).get(token_digest=digest_token(raw_token))
