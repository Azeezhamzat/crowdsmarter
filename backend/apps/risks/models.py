"""Explicit risks and human-owned response plans."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Risk(UUIDTimeStampedModel):
    """A decision risk assessed using transparent likelihood and impact ratings."""

    class ResponseStrategy(models.TextChoices):
        ACCEPT = "accept", "Accept"
        AVOID = "avoid", "Avoid"
        MITIGATE = "mitigate", "Mitigate"
        TRANSFER = "transfer", "Transfer"
        MONITOR = "monitor", "Monitor"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        MONITORING = "monitoring", "Monitoring"
        MITIGATED = "mitigated", "Mitigated"
        ACCEPTED = "accepted", "Accepted"
        CLOSED = "closed", "Closed"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="risks"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="risks"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="risks",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=240)
    description = models.TextField()
    likelihood = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    impact = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    response_strategy = models.CharField(max_length=20, choices=ResponseStrategy.choices)
    mitigation_plan = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_decision_risks",
    )
    review_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decision_risks",
    )

    class Meta:
        ordering = ["-likelihood", "-impact", "title", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="risk_title_not_empty"),
            models.CheckConstraint(
                condition=models.Q(likelihood__gte=1, likelihood__lte=5),
                name="risk_likelihood_between_1_and_5",
            ),
            models.CheckConstraint(
                condition=models.Q(impact__gte=1, impact__lte=5),
                name="risk_impact_between_1_and_5",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    response_strategy__in=["accept", "avoid", "mitigate", "transfer", "monitor"]
                ),
                name="risk_response_strategy_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "open",
                        "monitoring",
                        "mitigated",
                        "accepted",
                        "closed",
                    ]
                ),
                name="risk_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["decision", "status"], name="risk_decision_status_idx"),
            models.Index(fields=["organisation", "status"], name="risk_org_status_idx"),
        ]

    @property
    def score(self) -> int:
        """Return the transparent likelihood × impact score."""
        return self.likelihood * self.impact

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.mitigation_plan = self.mitigation_plan.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The risk must share the decision organisation."}
                )
        if self.option_id and self.option.decision_id != self.decision_id:
            raise ValidationError({"option": "The option must belong to this decision."})
        if (
            self.response_strategy
            in {
                self.ResponseStrategy.AVOID,
                self.ResponseStrategy.MITIGATE,
                self.ResponseStrategy.TRANSFER,
            }
            and not self.mitigation_plan
        ):
            raise ValidationError(
                {"mitigation_plan": "This response strategy requires an action plan."}
            )

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.title}"
