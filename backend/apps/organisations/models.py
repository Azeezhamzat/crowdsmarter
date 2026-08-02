"""Organisation tenant and membership models."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator

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
    """A customer-owned tenant boundary and its administrative policy."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        DEACTIVATED = "deactivated", "Deactivated"

    class InvitationPolicy(models.TextChoices):
        OWNERS_AND_ADMINS = "owners_and_admins", "Owners and administrators"
        OWNERS_ONLY = "owners_only", "Owners only"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    brand_name = models.CharField(max_length=120, blank=True)
    primary_colour = models.CharField(
        max_length=7,
        default="#315c54",
        validators=[RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use a six-digit hexadecimal colour.")],
    )
    invitation_policy = models.CharField(
        max_length=30, choices=InvitationPolicy.choices, default=InvitationPolicy.OWNERS_AND_ADMINS
    )
    default_invitation_role = models.CharField(
        max_length=20, choices=[("admin", "Administrator"), ("contributor", "Contributor"), ("viewer", "Viewer")],
        default="contributor",
    )
    retention_days = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="deactivated_organisations",
        null=True, blank=True,
    )
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
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "deactivated"]),
                name="organisation_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(invitation_policy__in=["owners_and_admins", "owners_only"]),
                name="organisation_invitation_policy_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(default_invitation_role__in=["admin", "contributor", "viewer"]),
                name="organisation_default_invite_role_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="active", deactivated_at__isnull=True, deactivated_by__isnull=True)
                    | models.Q(status="deactivated", deactivated_at__isnull=False, deactivated_by__isnull=False)
                ),
                name="organisation_deactivation_state_consistent",
            ),
        ]

    def clean(self) -> None:
        """Normalise stable organisation identity fields."""
        super().clean()
        self.name = self.name.strip()
        self.slug = self.slug.strip().lower()
        self.description = self.description.strip()
        self.website_url = self.website_url.strip()
        self.brand_name = self.brand_name.strip()
        self.primary_colour = self.primary_colour.strip().lower()

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


class MembershipEvent(UUIDTimeStampedModel):
    """Append-only administrative history for organisation membership and ownership."""

    class Kind(models.TextChoices):
        CREATED = "created", "Created"
        ROLE_CHANGED = "role_changed", "Role changed"
        REMOVED = "removed", "Removed"
        OWNERSHIP_TRANSFERRED = "ownership_transferred", "Ownership transferred"
        STATUS_CHANGED = "status_changed", "Status changed"

    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name="membership_events")
    membership_id_snapshot = models.UUIDField(null=True, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="organisation_membership_events"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="performed_membership_events"
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    previous_role = models.CharField(max_length=20, blank=True)
    new_role = models.CharField(max_length=20, blank=True)
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20, blank=True)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["created", "role_changed", "removed", "ownership_transferred", "status_changed"]),
                name="membership_event_kind_valid",
            ),
        ]
        indexes = [models.Index(fields=["organisation", "-created_at"], name="member_event_org_idx")]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValueError("Membership history is append-only.")
        super().save(*args, **kwargs)


class OrganisationDeletionRequest(UUIDTimeStampedModel):
    """Safeguarded request for later manual tenant deletion."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CANCELLED = "cancelled", "Cancelled"
        COMPLETED = "completed", "Completed"

    organisation = models.ForeignKey(Organisation, on_delete=models.PROTECT, related_name="deletion_requests")
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_organisation_deletions"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reason = models.TextField()
    earliest_deletion_at = models.DateTimeField()
    cancelled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="cancelled_organisation_deletions",
        null=True, blank=True,
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "cancelled", "completed"]),
                name="organisation_deletion_status_valid",
            ),
            models.UniqueConstraint(
                fields=["organisation"], condition=models.Q(status="pending"),
                name="one_pending_deletion_request_per_org",
            ),
        ]
