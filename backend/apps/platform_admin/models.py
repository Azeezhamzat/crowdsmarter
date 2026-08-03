"""Models for CrowdSmarter platform administration and governed support access."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class PlatformAdministrator(UUIDTimeStampedModel):
    """An explicit platform-level capability, separate from Django superuser flags."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="platform_administrator",
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    rationale = models.TextField()
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_platform_administrator_roles",
        null=True,
        blank=True,
    )
    suspended_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="suspended_platform_administrator_roles",
        null=True,
        blank=True,
    )
    suspended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["user__email"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "suspended"]),
                name="platform_administrator_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="active", suspended_by__isnull=True, suspended_at__isnull=True)
                    | models.Q(status="suspended", suspended_by__isnull=False, suspended_at__isnull=False)
                ),
                name="platform_administrator_suspension_consistent",
            ),
            models.CheckConstraint(
                condition=~models.Q(rationale=""),
                name="platform_administrator_rationale_not_empty",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.rationale = self.rationale.strip()
        if not self.rationale:
            raise ValidationError({"rationale": "Record why this platform capability is required."})

    @property
    def is_active(self) -> bool:
        return self.status == self.Status.ACTIVE and self.user.is_active

    def __str__(self) -> str:
        return f"{self.user.email} ({self.status})"


class PlatformConfiguration(UUIDTimeStampedModel):
    """Singleton operational contact and support-access policy."""

    class AIProviderKey(models.TextChoices):
        RULES = "rules", "Transparent rules (no external service)"
        ANTHROPIC = "anthropic", "Anthropic Claude"

    singleton_key = models.PositiveSmallIntegerField(default=1, unique=True, editable=False)
    public_contact_email = models.EmailField(default="hello@crowdsmarter.com")
    demo_email = models.EmailField(default="hello@crowdsmarter.com")
    support_email = models.EmailField(default="hello@crowdsmarter.com")
    privacy_email = models.EmailField(default="hello@crowdsmarter.com")
    security_email = models.EmailField(default="hello@crowdsmarter.com")
    notification_sender_email = models.EmailField(default="hello@crowdsmarter.com")
    support_access_max_hours = models.PositiveSmallIntegerField(default=8)
    ai_provider_key = models.CharField(
        max_length=20, choices=AIProviderKey.choices, default=AIProviderKey.RULES
    )
    ai_provider_model = models.CharField(max_length=100, default="claude-sonnet-5")
    ai_provider_api_key_encrypted = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "platform configuration"
        verbose_name_plural = "platform configuration"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(singleton_key=1),
                name="platform_configuration_singleton_key_one",
            ),
            models.CheckConstraint(
                condition=models.Q(support_access_max_hours__gte=1)
                & models.Q(support_access_max_hours__lte=72),
                name="platform_support_access_hours_range",
            ),
            models.CheckConstraint(
                condition=models.Q(ai_provider_key__in=["rules", "anthropic"]),
                name="platform_ai_provider_key_valid",
            ),
        ]

    @classmethod
    def load(cls) -> "PlatformConfiguration":
        item, _ = cls.objects.get_or_create(singleton_key=1)
        return item

    @property
    def ai_provider_api_key_is_set(self) -> bool:
        return bool(self.ai_provider_api_key_encrypted)

    def clean(self) -> None:
        super().clean()
        for field in (
            "public_contact_email",
            "demo_email",
            "support_email",
            "privacy_email",
            "security_email",
            "notification_sender_email",
        ):
            setattr(self, field, getattr(self, field).strip().lower())
        if (
            self.ai_provider_key == self.AIProviderKey.ANTHROPIC
            and not self.ai_provider_api_key_encrypted
        ):
            raise ValidationError(
                {
                    "ai_provider_key": (
                        "Set an Anthropic API key before selecting this provider."
                    )
                }
            )

    def __str__(self) -> str:
        return "CrowdSmarter platform configuration"


class SupportAccessGrant(UUIDTimeStampedModel):
    """Time-bounded, attributable support visibility into one tenant."""

    class AccessLevel(models.TextChoices):
        READ_ONLY = "read_only", "Read-only support"
        OPERATIONAL = "operational", "Operational support"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    administrator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="platform_support_access_grants",
    )
    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="platform_support_access_grants",
    )
    access_level = models.CharField(
        max_length=20,
        choices=AccessLevel.choices,
        default=AccessLevel.READ_ONLY,
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    expires_at = models.DateTimeField()
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="revoked_platform_support_access_grants",
        null=True,
        blank=True,
    )
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(access_level__in=["read_only", "operational"]),
                name="support_access_level_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "revoked", "expired"]),
                name="support_access_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(reason=""),
                name="support_access_reason_not_empty",
            ),
            # Keep the Q tree structurally identical to migration 0001. Django compares
            # serialized constraint state, not only SQL equivalence, during migration checks.
            models.CheckConstraint(
                condition=models.Q(
                    models.Q(
                        ("status", "active"),
                        ("revoked_at__isnull", True),
                        ("revoked_by__isnull", True),
                    ),
                    models.Q(
                        ("status", "expired"),
                        ("revoked_at__isnull", True),
                        ("revoked_by__isnull", True),
                    ),
                    models.Q(
                        ("status", "revoked"),
                        ("revoked_at__isnull", False),
                        ("revoked_by__isnull", False),
                    ),
                    _connector="OR",
                ),
                name="support_access_revocation_consistent",
            ),
        ]
        indexes = [
            models.Index(
                fields=["administrator", "status", "expires_at"],
                name="support_admin_status_exp_idx",
            ),
            models.Index(
                fields=["organisation", "status", "expires_at"],
                name="support_org_status_exp_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.reason = self.reason.strip()
        if len(self.reason) < 12:
            raise ValidationError({"reason": "Record a specific support-access reason."})
        if self.expires_at <= timezone.now():
            raise ValidationError({"expires_at": "Support access must expire in the future."})

    @property
    def is_current(self) -> bool:
        return self.status == self.Status.ACTIVE and self.expires_at > timezone.now()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.status == self.Status.ACTIVE and self.expires_at <= timezone.now():
            self.status = self.Status.EXPIRED
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.administrator.email} → {self.organisation.name} ({self.status})"
