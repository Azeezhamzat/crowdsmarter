"""In-application notifications for attributable workflow events."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class Notification(UUIDTimeStampedModel):
    """A tenant-scoped message delivered to one user inside the product."""

    class Kind(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        LIFECYCLE = "lifecycle", "Lifecycle"
        REVIEW_DUE = "review_due", "Review Due"
        AI_REVIEW = "ai_review", "AI Review"
        MEMBERSHIP = "membership", "Membership"
        COLLABORATION = "collaboration", "Collaboration"
        SYSTEM = "system", "System"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.CASCADE,
        related_name="notifications",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    title = models.CharField(max_length=240)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    dedup_key = models.CharField(max_length=180, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="notification_title_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    kind__in=[
                        "assignment",
                        "lifecycle",
                        "review_due",
                        "ai_review",
                        "membership",
                        "collaboration",
                        "system",
                    ]
                ),
                name="notification_kind_valid",
            ),
            models.UniqueConstraint(
                fields=["recipient", "dedup_key"],
                condition=~models.Q(dedup_key=""),
                name="notification_recipient_dedup_unique",
            ),
        ]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="notification_inbox_idx",
            ),
            models.Index(
                fields=["organisation", "-created_at"],
                name="notification_org_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.message = self.message.strip()
        self.url = self.url.strip()
        self.dedup_key = self.dedup_key.strip()
        if self.decision_id and self.decision.organisation_id != self.organisation_id:
            raise ValidationError(
                {"decision": "The notification decision must share the organisation."}
            )

    @property
    def is_read(self) -> bool:
        return self.read_at is not None

    def mark_read(self) -> None:
        if self.read_at is None:
            self.read_at = timezone.now()

    def __str__(self) -> str:
        return f"{self.recipient.email}: {self.title}"
