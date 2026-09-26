"""Immutable stakeholder recommendations within governed decisions."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel
from apps.participants.models import Participant


class PositionQuerySet(models.QuerySet["Position"]):
    """Prevent mutation of submitted stakeholder positions."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Submitted positions are immutable.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Submitted positions are immutable.")


class Position(UUIDTimeStampedModel):
    """One immutable version of a participant's decision recommendation."""

    class Recommendation(models.TextChoices):
        SUPPORT = "support", "Support"
        SUPPORT_WITH_CONDITIONS = (
            "support_with_conditions",
            "Support with conditions",
        )
        DO_NOT_SUPPORT_ANY = "do_not_support_any", "Do not support any option"
        ABSTAIN = "abstain", "Abstain"

    class Confidence(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="stakeholder_positions",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.PROTECT,
        related_name="stakeholder_positions",
    )
    participant = models.ForeignKey(
        "participants.Participant",
        on_delete=models.PROTECT,
        related_name="position_versions",
    )
    participant_role = models.CharField(
        max_length=30,
        choices=Participant.Role.choices,
    )
    preferred_option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="stakeholder_positions",
        null=True,
        blank=True,
    )
    recommendation = models.CharField(
        max_length=40,
        choices=Recommendation.choices,
    )
    rationale = models.TextField()
    conditions = models.TextField(blank=True)
    confidence = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        default=Confidence.MEDIUM,
    )
    version = models.PositiveIntegerField()
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_positions",
    )

    objects = PositionQuerySet.as_manager()

    class Meta:
        ordering = ["participant__user__email", "-version", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "participant", "version"],
                name="unique_position_version_per_participant",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    recommendation__in=[
                        "support",
                        "support_with_conditions",
                        "do_not_support_any",
                        "abstain",
                    ]
                ),
                name="position_recommendation_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(confidence__in=["low", "medium", "high"]),
                name="position_confidence_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1),
                name="position_version_positive",
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "participant", "-version"],
                name="position_decision_person_idx",
            ),
            models.Index(
                fields=["organisation", "-created_at"],
                name="position_org_created_idx",
            ),
        ]

    def clean(self) -> None:
        """Normalise text and enforce cross-domain position invariants."""
        super().clean()
        self.rationale = self.rationale.strip()
        self.conditions = self.conditions.strip()
        errors: dict[str, str] = {}
        if not self.rationale:
            errors["rationale"] = "A position rationale is required."
        if self.participant_id and self.decision_id:
            if self.participant.decision_id != self.decision_id:
                errors["participant"] = "The participant must belong to this decision."
            if self.participant.organisation_id != self.organisation_id:
                errors["organisation"] = "The participant must share the organisation."
            if self.submitted_by_id != self.participant.user_id:
                errors["submitted_by"] = "A participant may submit only their own position."
            if self._state.adding and self.participant_role != self.participant.role:
                errors["participant_role"] = (
                    "The recorded role must match the participant role at submission."
                )
        if self.preferred_option_id:
            if self.preferred_option.decision_id != self.decision_id:
                errors["preferred_option"] = "The option must belong to this decision."
            if self.preferred_option.organisation_id != self.organisation_id:
                errors["preferred_option"] = "The option must share the organisation."
        option_required = self.recommendation in {
            self.Recommendation.SUPPORT,
            self.Recommendation.SUPPORT_WITH_CONDITIONS,
        }
        if option_required and not self.preferred_option_id:
            errors["preferred_option"] = "Select the option this position supports."
        if not option_required and self.preferred_option_id:
            errors["preferred_option"] = (
                "Do not select an option when abstaining or rejecting all options."
            )
        if (
            self.recommendation == self.Recommendation.SUPPORT_WITH_CONDITIONS
            and not self.conditions
        ):
            errors["conditions"] = "Record the conditions attached to this support."
        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding is False:
            raise ValidationError("Submitted positions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Submitted positions are immutable.")

    def __str__(self) -> str:
        return f"{self.participant.user.email}: v{self.version} {self.get_recommendation_display()}"
