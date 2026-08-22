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

    class Reversibility(models.TextChoices):
        EASILY_REVERSIBLE = "easily_reversible", "Easily reversible"
        PARTIALLY_REVERSIBLE = "partially_reversible", "Partially reversible"
        DIFFICULT_TO_REVERSE = "difficult_to_reverse", "Difficult to reverse"
        IRREVERSIBLE = "irreversible", "Irreversible"

    class EligibilityStatus(models.TextChoices):
        PENDING = "pending", "Pending review"
        ELIGIBLE = "eligible", "Eligible"
        INELIGIBLE = "ineligible", "Ineligible"

    class OutcomeStatus(models.TextChoices):
        PENDING = "pending", "Pending decision"
        FUNDED = "funded", "Funded"
        DECLINED = "declined", "Declined"

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
    estimated_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Estimated cost in the organisation's reporting currency.",
    )
    cost_notes = models.TextField(blank=True)
    resource_notes = models.TextField(blank=True)
    implementation_time_estimate = models.CharField(
        max_length=120, blank=True, help_text="Plain-language estimate, e.g. '3-6 months'.",
    )
    reversibility = models.CharField(
        max_length=30, choices=Reversibility.choices, blank=True,
    )
    is_experiment = models.BooleanField(
        default=False,
        help_text="A bounded, minimum-viable way to test this option before committing further.",
    )
    experiment_notes = models.TextField(blank=True)
    depends_on = models.ManyToManyField(
        "self", symmetrical=False, related_name="required_by", blank=True,
        help_text="Options that must also be adopted for this option to work.",
    )
    mutually_exclusive_with = models.ManyToManyField(
        "self", symmetrical=True, blank=True,
        help_text="Options that cannot be selected together with this one.",
    )
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
    eligibility_status = models.CharField(
        max_length=20,
        choices=EligibilityStatus.choices,
        default=EligibilityStatus.PENDING,
    )
    eligibility_note = models.TextField(blank=True)
    eligibility_decided_at = models.DateTimeField(null=True, blank=True)
    eligibility_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eligibility_decisions",
        null=True,
        blank=True,
    )
    outcome_status = models.CharField(
        max_length=20,
        choices=OutcomeStatus.choices,
        default=OutcomeStatus.PENDING,
    )
    awarded_amount = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True,
        help_text="Amount funded, only meaningful once outcome_status is 'funded'.",
    )
    outcome_note = models.TextField(blank=True)
    outcome_decided_at = models.DateTimeField(null=True, blank=True)
    outcome_decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="outcome_decisions",
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
            models.CheckConstraint(
                condition=models.Q(eligibility_status__in=['pending', 'eligible', 'ineligible']),
                name="decision_option_eligibility_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(outcome_status__in=['pending', 'funded', 'declined']),
                name="decision_option_outcome_status_valid",
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
        self.cost_notes = self.cost_notes.strip()
        self.resource_notes = self.resource_notes.strip()
        self.implementation_time_estimate = self.implementation_time_estimate.strip()
        self.experiment_notes = self.experiment_notes.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The option must share the decision organisation."}
                )
        if self.status == self.Status.ACTIVE and (self.withdrawn_at or self.withdrawn_by_id):
            raise ValidationError("Active options cannot contain withdrawal metadata.")
        if self.status == self.Status.WITHDRAWN and not self.withdrawn_at:
            raise ValidationError("Withdrawn options require a withdrawal timestamp.")
        if self.is_experiment and not self.experiment_notes:
            raise ValidationError(
                {"experiment_notes": "Describe the bounded experiment this option represents."}
            )
        if self.eligibility_status == self.EligibilityStatus.PENDING and (
            self.eligibility_decided_at or self.eligibility_decided_by_id
        ):
            raise ValidationError("Pending eligibility cannot contain decision metadata.")
        if self.eligibility_status != self.EligibilityStatus.PENDING and not self.eligibility_decided_at:
            raise ValidationError("A decided eligibility status requires a decision timestamp.")
        if self.outcome_status == self.OutcomeStatus.PENDING and (
            self.outcome_decided_at or self.outcome_decided_by_id or self.awarded_amount is not None
        ):
            raise ValidationError("Pending outcome cannot contain decision metadata or an amount.")
        if self.outcome_status != self.OutcomeStatus.PENDING and not self.outcome_decided_at:
            raise ValidationError("A decided outcome status requires a decision timestamp.")
        if self.outcome_status == self.OutcomeStatus.FUNDED and self.awarded_amount is None:
            raise ValidationError(
                {"awarded_amount": "A funded outcome requires an awarded amount."}
            )
        if self.awarded_amount is not None and self.awarded_amount < 0:
            raise ValidationError({"awarded_amount": "The awarded amount cannot be negative."})

    def mark_status(self, *, status: str, actor) -> None:  # type: ignore[no-untyped-def]
        """Apply explicit soft-state metadata before validation."""
        self.status = status
        if status == self.Status.WITHDRAWN:
            self.withdrawn_at = timezone.now()
            self.withdrawn_by = actor
        else:
            self.withdrawn_at = None
            self.withdrawn_by = None

    def mark_eligibility(self, *, eligibility_status: str, eligibility_note: str, actor) -> None:  # type: ignore[no-untyped-def]
        """Apply explicit eligibility screening metadata before validation."""
        self.eligibility_status = eligibility_status
        self.eligibility_note = eligibility_note
        if eligibility_status == self.EligibilityStatus.PENDING:
            self.eligibility_decided_at = None
            self.eligibility_decided_by = None
        else:
            self.eligibility_decided_at = timezone.now()
            self.eligibility_decided_by = actor

    def mark_outcome(
        self, *, outcome_status: str, awarded_amount, outcome_note: str, actor
    ) -> None:  # type: ignore[no-untyped-def]
        """Apply explicit funding outcome metadata before validation."""
        self.outcome_status = outcome_status
        self.outcome_note = outcome_note
        if outcome_status == self.OutcomeStatus.PENDING:
            self.outcome_decided_at = None
            self.outcome_decided_by = None
            self.awarded_amount = None
        else:
            self.outcome_decided_at = timezone.now()
            self.outcome_decided_by = actor
            self.awarded_amount = awarded_amount if outcome_status == self.OutcomeStatus.FUNDED else None

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.title}"
