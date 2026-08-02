"""Alternatives considered within a governed decision."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class DecisionOption(UUIDTimeStampedModel):
    """A candidate course of action, including the status quo where relevant."""

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        WITHDRAWN = "withdrawn", "Withdrawn"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decision_options",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.CASCADE,
        related_name="options",
    )
    title = models.CharField(max_length=240)
    description = models.TextField()
    expected_benefits = models.TextField(blank=True)
    tradeoffs = models.TextField(blank=True)
    is_status_quo = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="proposed_decision_options",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decision_options",
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="withdrawn_decision_options",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-is_status_quo", "created_at", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="decision_option_title_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=['active', 'withdrawn']),
                name="decision_option_status_valid",
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="active", is_status_quo=True),
                name="one_active_status_quo_option_per_decision",
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "status", "created_at"],
                name="option_decision_status_idx",
            ),
            models.Index(
                fields=["organisation", "status"],
                name="option_org_status_idx",
            ),
        ]

    def clean(self) -> None:
        """Normalise content and enforce tenant and withdrawal invariants."""
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.expected_benefits = self.expected_benefits.strip()
        self.tradeoffs = self.tradeoffs.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The option must share the decision organisation."}
                )
        if self.status == self.Status.ACTIVE and (self.withdrawn_at or self.withdrawn_by_id):
            raise ValidationError("Active options cannot contain withdrawal metadata.")
        if self.status == self.Status.WITHDRAWN and not self.withdrawn_at:
            raise ValidationError("Withdrawn options require a withdrawal timestamp.")

    def mark_status(self, *, status: str, actor) -> None:  # type: ignore[no-untyped-def]
        """Apply explicit soft-state metadata before validation."""
        self.status = status
        if status == self.Status.WITHDRAWN:
            self.withdrawn_at = timezone.now()
            self.withdrawn_by = actor
        else:
            self.withdrawn_at = None
            self.withdrawn_by = None

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.title}"
