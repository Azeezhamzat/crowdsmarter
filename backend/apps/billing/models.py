"""Plan entitlements and per-organisation subscription records.

No payment processing lives here — see ADR 0031. These models record which
packaging tier an organisation is on and enforce simple, self-contained
usage limits; a real payment-provider integration would extend
`OrganisationSubscription` with a provider reference, not replace it.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class Plan(UUIDTimeStampedModel):
    """A named packaging tier. Nullable limits mean unlimited."""

    class SupportLevel(models.TextChoices):
        COMMUNITY = "community", "Community"
        STANDARD = "standard", "Standard"
        PRIORITY = "priority", "Priority"

    key = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    trial_days = models.PositiveIntegerField(default=14)
    max_active_decisions = models.PositiveIntegerField(null=True, blank=True)
    max_active_members = models.PositiveIntegerField(null=True, blank=True)
    includes_advanced_foresight = models.BooleanField(default=True)
    includes_ai_assistance = models.BooleanField(default=True)
    support_level = models.CharField(
        max_length=20, choices=SupportLevel.choices, default=SupportLevel.COMMUNITY
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(key=""), name="plan_key_not_empty"),
            models.CheckConstraint(condition=~models.Q(name=""), name="plan_name_not_empty"),
        ]

    def clean(self) -> None:
        super().clean()
        self.key = self.key.strip().lower()
        self.name = self.name.strip()
        self.description = self.description.strip()

    def __str__(self) -> str:
        return self.name


class OrganisationSubscription(UUIDTimeStampedModel):
    """The single active plan assignment for one organisation."""

    class Status(models.TextChoices):
        TRIALING = "trialing", "Trialing"
        ACTIVE = "active", "Active"
        EXPIRED = "expired", "Expired"

    organisation = models.OneToOneField(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIALING)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    billing_contact = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="billing_contact_for",
        null=True,
        blank=True,
    )
    started_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_subscriptions"
    )

    class Meta:
        indexes = [
            models.Index(fields=["organisation", "status"], name="billing_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        if (
            self.billing_contact_id
            and self.organisation_id
            and not self.organisation.memberships.filter(
                user_id=self.billing_contact_id, status="active"
            ).exists()
        ):
            raise ValidationError(
                {"billing_contact": "The billing contact must be an active organisation member."}
            )

    @property
    def is_trial_expired(self) -> bool:
        return bool(
            self.status == self.Status.TRIALING
            and self.trial_ends_at
            and self.trial_ends_at < timezone.now()
        )

    def __str__(self) -> str:
        return f"{self.organisation.name}: {self.plan.name} ({self.status})"
