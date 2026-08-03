"""Tenant-safe billing reads."""

from __future__ import annotations

from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.accounts.models import User
from apps.organisations.selectors import organisation_for_user

from .models import OrganisationSubscription, Plan


def active_plans() -> QuerySet[Plan]:
    return Plan.objects.filter(is_active=True).order_by("order")


def subscription_for_user(*, user: User, organisation_id: UUID) -> OrganisationSubscription:
    organisation = organisation_for_user(user=user, organisation_id=organisation_id)
    return get_object_or_404(
        OrganisationSubscription.objects.select_related("plan", "billing_contact"),
        organisation=organisation,
    )
