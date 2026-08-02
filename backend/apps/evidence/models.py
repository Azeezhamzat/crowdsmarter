"""Attributable evidence used in organisational decisions."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class Evidence(UUIDTimeStampedModel):
    """A source-backed claim or observation relevant to a decision or option."""

    class SourceType(models.TextChoices):
        RESEARCH = "research", "Research"
        INTERNAL_DATA = "internal_data", "Internal Data"
        EXPERT_JUDGEMENT = "expert_judgement", "Expert Judgement"
        STAKEHOLDER_INPUT = "stakeholder_input", "Stakeholder Input"
        POLICY = "policy", "Policy or Regulation"
        OTHER = "other", "Other"

    class Stance(models.TextChoices):
        SUPPORTS = "supports", "Supports"
        CHALLENGES = "challenges", "Challenges"
        MIXED = "mixed", "Mixed"
        CONTEXT = "context", "Context"

    class Strength(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        WITHDRAWN = "withdrawn", "Withdrawn"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="evidence_items"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="evidence_items"
    )
    source = models.ForeignKey(
        "foresight.Source",
        on_delete=models.PROTECT,
        related_name="decision_evidence",
        null=True,
        blank=True,
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="evidence_items",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=240)
    summary = models.TextField()
    source_type = models.CharField(max_length=40, choices=SourceType.choices)
    source_reference = models.CharField(max_length=500, blank=True)
    source_url = models.URLField(max_length=1000, blank=True)
    stance = models.CharField(max_length=20, choices=Stance.choices)
    strength = models.CharField(
        max_length=20, choices=Strength.choices, default=Strength.MODERATE
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_evidence_items",
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="withdrawn_evidence_items",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""), name="evidence_title_not_empty"
            ),
            models.CheckConstraint(
                condition=models.Q(
                    source_type__in=[
                        'research',
                        'internal_data',
                        'expert_judgement',
                        'stakeholder_input',
                        'policy',
                        'other',
                    ]
                ),
                name="evidence_source_type_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(stance__in=['supports', 'challenges', 'mixed', 'context']),
                name="evidence_stance_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(strength__in=['low', 'moderate', 'high']),
                name="evidence_strength_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=['active', 'withdrawn']),
                name="evidence_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["decision", "status", "stance"], name="evidence_decision_idx"),
            models.Index(fields=["organisation", "status"], name="evidence_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.summary = self.summary.strip()
        self.source_reference = self.source_reference.strip()
        self.source_url = self.source_url.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The evidence must share the decision organisation."}
                )
        if self.source_id and self.source.organisation_id != self.organisation_id:
            raise ValidationError({"source": "The source must share the organisation."})
        if self.option_id:
            if self.option.decision_id != self.decision_id:
                raise ValidationError({"option": "The option must belong to this decision."})
            if self.option.organisation_id != self.organisation_id:
                raise ValidationError({"option": "The option must share the organisation."})
        if not self.source_id and not self.source_reference and not self.source_url:
            raise ValidationError(
                {"source_reference": "Provide a structured source, source reference, or source URL."}
            )
        if self.status == self.Status.ACTIVE and (self.withdrawn_at or self.withdrawn_by_id):
            raise ValidationError("Active evidence cannot contain withdrawal metadata.")
        if self.status == self.Status.WITHDRAWN and not self.withdrawn_at:
            raise ValidationError("Withdrawn evidence requires a withdrawal timestamp.")

    def mark_status(self, *, status: str, actor) -> None:  # type: ignore[no-untyped-def]
        self.status = status
        if status == self.Status.WITHDRAWN:
            self.withdrawn_at = timezone.now()
            self.withdrawn_by = actor
        else:
            self.withdrawn_at = None
            self.withdrawn_by = None

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.title}"
