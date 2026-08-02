"""Accountable commitment, implementation, and outcome-review records."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class DecisionReview(UUIDTimeStampedModel):
    """The accountable execution and outcome record for one finalised decision."""

    class OutcomeAssessment(models.TextChoices):
        EXCEEDED = "exceeded", "Exceeded expectations"
        MET = "met", "Met expectations"
        PARTIALLY_MET = "partially_met", "Partially met expectations"
        NOT_MET = "not_met", "Did not meet expectations"
        INCONCLUSIVE = "inconclusive", "Inconclusive"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="decision_reviews",
    )
    decision = models.OneToOneField(
        "decisions.Decision",
        on_delete=models.PROTECT,
        related_name="review",
    )
    implementation_owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_decision_reviews",
    )
    commitment_statement = models.TextField()
    success_measures = models.TextField()
    review_due_date = models.DateField()
    commitment_rationale = models.TextField()
    commitment_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="recorded_decision_commitments",
    )
    commitment_recorded_at = models.DateTimeField(default=timezone.now)

    implementation_plan = models.TextField(blank=True)
    implementation_started_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="started_decision_implementations",
        null=True,
        blank=True,
    )
    implementation_started_at = models.DateTimeField(null=True, blank=True)

    implementation_summary = models.TextField(blank=True)
    outcome_summary = models.TextField(blank=True)
    outcome_assessment = models.CharField(
        max_length=30,
        choices=OutcomeAssessment.choices,
        blank=True,
    )
    review_evidence = models.TextField(blank=True)
    unintended_consequences = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="completed_decision_reviews",
        null=True,
        blank=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(commitment_statement=""),
                name="review_commitment_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(success_measures=""),
                name="review_measures_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(outcome_assessment="")
                | models.Q(
                    outcome_assessment__in=[
                        "exceeded",
                        "met",
                        "partially_met",
                        "not_met",
                        "inconclusive",
                    ]
                ),
                name="review_outcome_assessment_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "review_due_date"],
                name="review_org_due_idx",
            ),
            models.Index(
                fields=["implementation_owner", "review_due_date"],
                name="review_owner_due_idx",
            ),
        ]

    def clean(self) -> None:
        """Normalise text and protect tenant and accountability invariants."""
        super().clean()
        text_fields = [
            "commitment_statement",
            "success_measures",
            "commitment_rationale",
            "implementation_plan",
            "implementation_summary",
            "outcome_summary",
            "review_evidence",
            "unintended_consequences",
        ]
        for field in text_fields:
            setattr(self, field, getattr(self, field).strip())
        errors: dict[str, str] = {}
        if not self.commitment_statement:
            errors["commitment_statement"] = "A clear commitment is required."
        if not self.success_measures:
            errors["success_measures"] = "Define how the outcome will be judged."
        if not self.commitment_rationale:
            errors["commitment_rationale"] = "Record why this commitment is appropriate."
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                errors["organisation"] = "The review must share the decision organisation."
        if self.implementation_owner_id and self.organisation_id:
            owner_is_member = self.organisation.memberships.filter(
                user_id=self.implementation_owner_id,
                status="active",
            ).exists()
            if not owner_is_member:
                errors["implementation_owner"] = (
                    "The implementation owner must be an active organisation member."
                )
        if self.reviewed_at and not self.reviewed_by_id:
            errors["reviewed_by"] = "A completed review requires an accountable reviewer."
        if self.reviewed_by_id and not self.reviewed_at:
            errors["reviewed_at"] = "A completed review requires a completion time."
        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"Outcome review: {self.decision.title}"
