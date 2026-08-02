"""Reusable organisational learning captured after outcome review."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Lesson(UUIDTimeStampedModel):
    """One attributable lesson that can inform future decisions."""

    class Category(models.TextChoices):
        PROCESS = "process", "Decision process"
        EVIDENCE = "evidence", "Evidence quality"
        ASSUMPTION = "assumption", "Assumption"
        STAKEHOLDER = "stakeholder", "Stakeholder involvement"
        IMPLEMENTATION = "implementation", "Implementation"
        OUTCOME = "outcome", "Outcome"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.PROTECT,
        related_name="lessons",
    )
    title = models.CharField(max_length=240)
    insight = models.TextField()
    category = models.CharField(max_length=30, choices=Category.choices)
    applicability = models.TextField()
    recommended_change = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_lessons",
    )
    retired_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="retired_lessons",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="lesson_title_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(insight=""),
                name="lesson_insight_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(applicability=""),
                name="lesson_applicability_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    category__in=[
                        "process",
                        "evidence",
                        "assumption",
                        "stakeholder",
                        "implementation",
                        "outcome",
                        "other",
                    ]
                ),
                name="lesson_category_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "retired"]),
                name="lesson_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-created_at"],
                name="lesson_org_status_idx",
            ),
            models.Index(
                fields=["decision", "status", "-created_at"],
                name="lesson_decision_status_idx",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.insight = self.insight.strip()
        self.applicability = self.applicability.strip()
        self.recommended_change = self.recommended_change.strip()
        errors: dict[str, str] = {}
        if not self.title:
            errors["title"] = "A concise lesson title is required."
        if not self.insight:
            errors["insight"] = "Record what the organisation learned."
        if not self.applicability:
            errors["applicability"] = "Explain when this lesson should be reused."
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                errors["organisation"] = "The lesson must share the decision organisation."
        if self.status == self.Status.RETIRED and not self.retired_by_id:
            errors["retired_by"] = "A retired lesson requires an accountable actor."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return self.title
