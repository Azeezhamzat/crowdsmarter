"""Organisation tenant and membership models."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class OrganisationQuerySet(models.QuerySet["Organisation"]):
    """Tenant-safe organisation queries."""

    def for_user(self, user: Any) -> models.QuerySet["Organisation"]:
        if user.is_anonymous:
            return self.none()
        return self.filter(
            memberships__user=user,
            memberships__status=Membership.Status.ACTIVE,
        ).distinct()


class Organisation(UUIDTimeStampedModel):
    """A customer-owned tenant boundary."""

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_organisations",
    )

    objects = OrganisationQuerySet.as_manager()

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="organisation_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(slug=""),
                name="organisation_slug_not_empty",
            ),
        ]

    def clean(self) -> None:
        """Normalise stable organisation identity fields."""
        super().clean()
        self.name = self.name.strip()
        self.slug = self.slug.strip().lower()

    def __str__(self) -> str:
        return self.name


class Membership(UUIDTimeStampedModel):
    """A user's explicit role within one organisation."""

    class Role(models.TextChoices):
        OWNER = "owner", "Owner"
        ADMIN = "admin", "Administrator"
        CONTRIBUTOR = "contributor", "Contributor"
        VIEWER = "viewer", "Viewer"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organisation_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["user__email"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "user"],
                name="unique_active_or_inactive_membership_per_user_org",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["owner", "admin", "contributor", "viewer"]),
                name="membership_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "suspended"]),
                name="membership_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "role", "status"],
                name="org_members_role_status_idx",
            ),
            models.Index(
                fields=["user", "status"],
                name="org_members_user_status_idx",
            ),
        ]

    @property
    def can_manage_members(self) -> bool:
        """Return whether the role may perform ordinary membership administration."""
        return self.status == self.Status.ACTIVE and self.role in {
            self.Role.OWNER,
            self.Role.ADMIN,
        }

    def __str__(self) -> str:
        return f"{self.user.email} in {self.organisation.name} ({self.role})"
