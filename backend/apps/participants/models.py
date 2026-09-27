"""Stakeholder participation in governed decisions."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class Participant(UUIDTimeStampedModel):
    """An organisation member with an explicit role in one decision."""

    class Role(models.TextChoices):
        DECISION_OWNER = "decision_owner", "Decision Owner"
        DECISION_MAKER = "decision_maker", "Decision Maker"
        CONTRIBUTOR = "contributor", "Contributor"
        REVIEWER = "reviewer", "Reviewer"
        OBSERVER = "observer", "Observer"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REMOVED = "removed", "Removed"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decision_participants",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.CASCADE,
        related_name="participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decision_participations",
    )
    role = models.CharField(max_length=30, choices=Role.choices)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="added_decision_participants",
    )
    removed_at = models.DateTimeField(null=True, blank=True)
    removed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="removed_decision_participants",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["role", "user__email", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "user"],
                condition=models.Q(status="active"),
                name="unique_active_participant_per_decision_user",
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="active", role="decision_owner"),
                name="one_active_owner_participant_per_decision",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    role__in=[
                        "decision_owner",
                        "decision_maker",
                        "contributor",
                        "reviewer",
                        "observer",
                    ]
                ),
                name="participant_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["active", "removed"]),
                name="participant_status_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "role"],
                name="participant_org_status_idx",
            ),
            models.Index(
                fields=["decision", "status", "role"],
                name="participant_decision_idx",
            ),
        ]

    def clean(self) -> None:
        """Protect direct organisation ownership and removal metadata."""
        super().clean()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The participant must share the decision organisation."}
                )
        if self.status == self.Status.ACTIVE and (self.removed_at or self.removed_by_id):
            raise ValidationError("Active participants cannot contain removal metadata.")
        if self.status == self.Status.REMOVED and not self.removed_at:
            raise ValidationError("Removed participants require a removal timestamp.")

    def __str__(self) -> str:
        return f"{self.user.email}: {self.get_role_display()} in {self.decision.title}"


class ConflictOfInterest(UUIDTimeStampedModel):
    """A reviewer's declared conflict, excluding their scoring from aggregate results."""

    class Scope(models.TextChoices):
        DECISION = "decision", "Entire round"
        OPTION = "option", "One application"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="conflicts_of_interest",
    )
    participant = models.ForeignKey(
        Participant,
        on_delete=models.CASCADE,
        related_name="conflicts_of_interest",
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.CASCADE,
        related_name="conflicts_of_interest",
        null=True,
        blank=True,
    )
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.OPTION)
    reason = models.TextField(blank=True)
    declared_at = models.DateTimeField()
    declared_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="declared_conflicts_of_interest",
    )
    withdrawn_at = models.DateTimeField(null=True, blank=True)
    withdrawn_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="withdrawn_conflicts_of_interest",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-declared_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(scope__in=["decision", "option"]),
                name="conflict_of_interest_scope_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(scope="option", option__isnull=False)
                    | models.Q(scope="decision", option__isnull=True)
                ),
                name="conflict_of_interest_option_required_iff_option_scope",
            ),
            models.UniqueConstraint(
                fields=["participant", "option"],
                condition=models.Q(withdrawn_at__isnull=True, scope="option"),
                name="unique_active_option_conflict_per_participant",
            ),
            models.UniqueConstraint(
                fields=["participant"],
                condition=models.Q(withdrawn_at__isnull=True, scope="decision"),
                name="unique_active_decision_conflict_per_participant",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "participant"],
                name="conflict_org_participant_idx",
            ),
        ]

    def clean(self) -> None:
        """Enforce tenant scope and option/decision consistency."""
        super().clean()
        self.reason = self.reason.strip()
        if self.participant_id and self.organisation_id:
            if self.participant.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The conflict must share the participant's organisation."}
                )
        if self.option_id and self.participant_id:
            if self.option.decision_id != self.participant.decision_id:
                raise ValidationError(
                    {"option": "The option must belong to the participant's decision."}
                )
        if self.withdrawn_at and not self.withdrawn_by_id:
            raise ValidationError("A withdrawn conflict requires who withdrew it.")
        if not self.withdrawn_at and self.withdrawn_by_id:
            raise ValidationError("Withdrawal metadata requires a withdrawal timestamp.")

    def __str__(self) -> str:
        target = self.option.title if self.option_id else "the entire round"
        return f"{self.participant.user.email} conflict on {target}"
