"""One organisation's choice of applicant-verification lookup provider."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class OrganisationLookupConfiguration(UUIDTimeStampedModel):
    class ProviderKey(models.TextChoices):
        MANUAL = "manual", "Manual verification"
        CANDID = "candid", "Candid (GuideStar)"

    organisation = models.OneToOneField(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="lookup_configuration"
    )
    provider_key = models.CharField(
        max_length=20, choices=ProviderKey.choices, default=ProviderKey.MANUAL
    )
    api_key_encrypted = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "organisation lookup configuration"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(provider_key__in=["manual", "candid"]),
                name="lookup_provider_key_valid",
            ),
        ]

    @property
    def api_key_is_set(self) -> bool:
        return bool(self.api_key_encrypted)

    def clean(self) -> None:
        super().clean()
        if self.provider_key == self.ProviderKey.CANDID and not self.api_key_encrypted:
            raise ValidationError({"provider_key": "Set an API key before selecting Candid."})

    def __str__(self) -> str:
        return f"{self.organisation.name}: {self.get_provider_key_display()}"
