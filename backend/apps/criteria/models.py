"""Standalone decision criteria: what matters, how it is weighed, and why."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Criterion(UUIDTimeStampedModel):
    """A named, weighted basis for comparing options on one decision.

    Criteria are defined independently of any evaluation or prioritisation
    exercise, so the values that matter can be agreed before scoring begins.
    """

    class Direction(models.TextChoices):
        MAXIMIZE = "maximize", "Higher is better"
        MINIMIZE = "minimize", "Lower is better"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="decision_criteria"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="criteria"
    )
    title = models.CharField(max_length=240)
    description = models.TextField()
    measurement_note = models.TextField(
        blank=True, help_text="How this is measured: scale, unit, or method."
    )
    direction = models.CharField(max_length=20, choices=Direction.choices)
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Relative weight from 0-100. Weights are compared, not required to sum to 100.",
    )
    weight_rationale = models.TextField(blank=True)
    is_must_have = models.BooleanField(
        default=False, help_text="An option failing this threshold cannot be selected."
    )
    threshold_note = models.TextField(
        blank=True, help_text="The minimum acceptable bar, in plain language."
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_decision_criteria",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decision_criteria",
    )
    order = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["order", "title", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="criterion_title_not_empty"),
            models.CheckConstraint(
                condition=models.Q(weight__gte=0, weight__lte=100),
                name="criterion_weight_between_0_and_100",
            ),
            models.CheckConstraint(
                condition=models.Q(direction__in=["maximize", "minimize"]),
                name="criterion_direction_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "retired"]),
                name="criterion_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["decision", "status"], name="criterion_decision_status_idx"),
            models.Index(fields=["organisation", "status"], name="criterion_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.measurement_note = self.measurement_note.strip()
        self.weight_rationale = self.weight_rationale.strip()
        self.threshold_note = self.threshold_note.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The criterion must share the decision organisation."}
                )
        if self.is_must_have and not self.threshold_note:
            raise ValidationError(
                {"threshold_note": "A must-have criterion requires a stated threshold."}
            )

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.title}"
