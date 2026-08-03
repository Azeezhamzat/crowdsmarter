"""Secure, organisation-controlled invitation records."""

from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models.functions import Lower

from apps.core.models import UUIDTimeStampedModel
from apps.organisations.models import Membership, Organisation


class OrganisationInvitation(UUIDTimeStampedModel):
    """A revocable invitation to create or connect an account to one tenant.

    Raw acceptance tokens are never persisted. ``token_digest`` stores a keyed
    digest so a database disclosure does not expose usable invitation links.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REVOKED = "revoked", "Revoked"

    organisation = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    email = models.EmailField(max_length=254)
    role = models.CharField(max_length=20, choices=Membership.Role.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    token_digest = models.CharField(max_length=64, unique=True)
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_organisation_invitations",
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="accepted_organisation_invitations",
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_sent_at = models.DateTimeField(null=True, blank=True)
    send_count = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                "organisation",
                name="unique_invite_email_ci_per_org",
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["owner", "admin", "contributor", "viewer"]),
                name="invitation_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "accepted", "revoked"]),
                name="invitation_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(email=""),
                name="invitation_email_not_empty",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        status="pending",
                        accepted_by__isnull=True,
                        accepted_at__isnull=True,
                        revoked_at__isnull=True,
                    )
                    | models.Q(
                        status="accepted",
                        accepted_by__isnull=False,
                        accepted_at__isnull=False,
                        revoked_at__isnull=True,
                    )
                    | models.Q(
                        status="revoked",
                        accepted_by__isnull=True,
                        accepted_at__isnull=True,
                        revoked_at__isnull=False,
                    )
                ),
                name="invitation_state_consistent",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-created_at"],
                name="invite_org_status_created_idx",
            ),
            models.Index(
                fields=["email", "status"],
                name="invite_email_status_idx",
            ),
            models.Index(fields=["expires_at"], name="invite_expires_idx"),
        ]

    def full_clean(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Normalise the invited identity before field-level validation runs."""
        self.email = self.email.strip().lower()
        return super().full_clean(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.email} invited to {self.organisation.name}"
