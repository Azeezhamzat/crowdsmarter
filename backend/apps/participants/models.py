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
                        'decision_owner',
                        'decision_maker',
                        'contributor',
                        'reviewer',
                        'observer',
                    ]
                ),
                name="participant_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=['active', 'removed']),
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
