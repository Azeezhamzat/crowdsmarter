"""Per-organisation disbursement configuration and the payout ledger for funded applications."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class OrganisationDisbursementConfiguration(UUIDTimeStampedModel):
    """One organisation's choice of payout provider, defaulting to a zero-dependency manual ledger."""

    class ProviderKey(models.TextChoices):
        MANUAL = "manual", "Manual ledger"
        STRIPE = "stripe", "Stripe Connect"

    organisation = models.OneToOneField(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="disbursement_configuration"
    )
    provider_key = models.CharField(max_length=20, choices=ProviderKey.choices, default=ProviderKey.MANUAL)
    stripe_account_id = models.CharField(max_length=100, blank=True, default="")
    api_key_encrypted = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "organisation disbursement configuration"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(provider_key__in=["manual", "stripe"]),
                name="disbursement_provider_key_valid",
            ),
        ]

    @property
    def api_key_is_set(self) -> bool:
        return bool(self.api_key_encrypted)

    def clean(self) -> None:
        super().clean()
        self.stripe_account_id = self.stripe_account_id.strip()
        if self.provider_key == self.ProviderKey.STRIPE and not (self.stripe_account_id and self.api_key_encrypted):
            raise ValidationError(
                {"provider_key": "Set a connected account and API key before selecting Stripe."}
            )

    def __str__(self) -> str:
        return f"{self.organisation.name}: {self.get_provider_key_display()}"


class Disbursement(UUIDTimeStampedModel):
    """One payout record against a funded application - the audit trail an organiser or funder can point to."""

    class Status(models.TextChoices):
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="disbursements"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption", on_delete=models.PROTECT, related_name="disbursements"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    provider_key = models.CharField(max_length=20, choices=OrganisationDisbursementConfiguration.ProviderKey.choices)
    status = models.CharField(max_length=20, choices=Status.choices)
    external_reference = models.CharField(max_length=200, blank=True, default="")
    note = models.TextField(blank=True)
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="issued_disbursements")

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="disbursement_amount_positive"),
        ]
        indexes = [
            models.Index(fields=["option", "-created_at"], name="disbursement_option_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.note = self.note.strip()
        if self.option_id and self.organisation_id and self.option.organisation_id != self.organisation_id:
            raise ValidationError({"organisation": "The disbursement must share the option's organisation."})

    def __str__(self) -> str:
        return f"{self.amount} to {self.option.title} ({self.status})"
