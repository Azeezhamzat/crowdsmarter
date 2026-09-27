"""Explicit assumptions that influence a governed decision."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Assumption(UUIDTimeStampedModel):
    """A testable belief whose failure may change the decision."""

    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    class VerificationStatus(models.TextChoices):
        UNVERIFIED = "unverified", "Unverified"
        PARTIALLY_VERIFIED = "partially_verified", "Partially Verified"
        VERIFIED = "verified", "Verified"
        INVALIDATED = "invalidated", "Invalidated"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RETIRED = "retired", "Retired"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="assumptions"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="assumptions"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="assumptions",
        null=True,
        blank=True,
    )
    statement = models.TextField()
    rationale = models.TextField(blank=True)
    impact_if_false = models.TextField()
    confidence = models.CharField(max_length=20, choices=Confidence.choices)
    verification_status = models.CharField(
        max_length=30,
        choices=VerificationStatus.choices,
        default=VerificationStatus.UNVERIFIED,
    )
    verification_notes = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_assumptions",
    )
    review_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assumptions",
    )

    class Meta:
        ordering = ["verification_status", "-confidence", "created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(statement=""), name="assumption_statement_not_empty"
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__in=["low", "medium", "high"]),
                name="assumption_confidence_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    verification_status__in=[
                        "unverified",
                        "partially_verified",
                        "verified",
                        "invalidated",
                    ]
                ),
                name="assumption_verification_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "retired"]),
                name="assumption_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "status", "verification_status"],
                name="assumption_decision_idx",
            ),
            models.Index(fields=["organisation", "status"], name="assumption_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.statement = self.statement.strip()
        self.rationale = self.rationale.strip()
        self.impact_if_false = self.impact_if_false.strip()
        self.verification_notes = self.verification_notes.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The assumption must share the decision organisation."}
                )
        if self.option_id and self.option.decision_id != self.decision_id:
            raise ValidationError({"option": "The option must belong to this decision."})
        if self.verification_status != self.VerificationStatus.UNVERIFIED:
            if not self.verification_notes:
                raise ValidationError(
                    {"verification_notes": "Verification notes are required for this status."}
                )

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.statement[:80]}"
