"""Attributable, reviewable AI assistance records."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class AIReview(UUIDTimeStampedModel):
    """One provider-generated advisory review of a decision snapshot."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="ai_reviews",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.PROTECT,
        related_name="ai_reviews",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_ai_reviews",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    provider_key = models.CharField(max_length=120)
    provider_label = models.CharField(max_length=240)
    model_identifier = models.CharField(max_length=240, blank=True)
    prompt_version = models.CharField(max_length=80, default="decision-review-v1")
    input_fingerprint = models.CharField(max_length=64)
    input_snapshot = models.JSONField(default=dict)
    output = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_ai_reviews",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    dismissed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="dismissed_ai_reviews",
        null=True,
        blank=True,
    )
    dismissed_at = models.DateTimeField(null=True, blank=True)
    dismissal_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["pending", "running", "completed", "failed"]),
                name="ai_review_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(provider_key=""),
                name="ai_review_provider_not_empty",
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "-created_at"],
                name="ai_review_decision_idx",
            ),
            models.Index(
                fields=["organisation", "status", "-created_at"],
                name="ai_review_org_status_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.provider_key = self.provider_key.strip()
        self.provider_label = self.provider_label.strip()
        self.model_identifier = self.model_identifier.strip()
        self.prompt_version = self.prompt_version.strip()
        self.error_message = self.error_message.strip()
        self.review_notes = self.review_notes.strip()
        self.dismissal_reason = self.dismissal_reason.strip()
        if self.decision_id and self.decision.organisation_id != self.organisation_id:
            raise ValidationError(
                {"organisation": "The AI review must share the decision organisation."}
            )
        if self.status == self.Status.COMPLETED and not self.output:
            raise ValidationError({"output": "A completed AI review requires output."})
        if self.status == self.Status.FAILED and not self.error_message:
            raise ValidationError(
                {"error_message": "A failed AI review requires an error message."}
            )
        if self.dismissed_at and not self.dismissal_reason:
            raise ValidationError({"dismissal_reason": "A dismissed review requires a reason."})

    @property
    def is_dismissed(self) -> bool:
        return self.dismissed_at is not None

    @property
    def is_reviewed(self) -> bool:
        return self.reviewed_at is not None

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.provider_label} ({self.status})"
