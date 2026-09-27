"""Core decision records and immutable lifecycle transitions."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class DecisionQuerySet(models.QuerySet["Decision"]):
    """Tenant-safe decision queries."""

    def for_user(self, user: Any) -> models.QuerySet[Decision]:
        if user.is_anonymous:
            return self.none()
        return self.filter(
            organisation__memberships__user=user,
            organisation__memberships__status="active",
        ).distinct()


class Decision(UUIDTimeStampedModel):
    """A governed organisational decision aggregate."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        FRAMING = "framing", "Framing"
        OPEN_FOR_CONTRIBUTION = "open_for_contribution", "Open for Contribution"
        UNDER_REVIEW = "under_review", "Under Review"
        READY_FOR_DECISION = "ready_for_decision", "Ready for Decision"
        DECISION_FINALISED = "decision_finalised", "Decision Finalised"
        COMMITMENT = "commitment", "Commitment"
        IMPLEMENTATION = "implementation", "Implementation"
        OUTCOME_REVIEW = "outcome_review", "Outcome Review"
        LESSONS_LEARNED = "lessons_learned", "Lessons Learned"
        ARCHIVED = "archived", "Archived"

    class Urgency(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.PROTECT,
        related_name="decisions",
    )
    title = models.CharField(max_length=240)
    decision_question = models.TextField(blank=True)
    purpose = models.TextField(blank=True)
    context = models.TextField(blank=True)
    scope = models.TextField(blank=True)
    contribution_guidance = models.TextField(blank=True)
    source_template_key = models.CharField(max_length=80, blank=True)
    source_template_version = models.PositiveSmallIntegerField(null=True, blank=True)
    source_method_version = models.ForeignKey(
        "methodology.DecisionMethodVersion",
        on_delete=models.PROTECT,
        related_name="decisions",
        null=True,
        blank=True,
    )
    urgency = models.CharField(
        max_length=20,
        choices=Urgency.choices,
        default=Urgency.NORMAL,
    )
    target_decision_date = models.DateField(null=True, blank=True)
    contribution_deadline = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=40,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    status_changed_at = models.DateTimeField(default=timezone.now)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_decisions",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decisions",
    )

    objects = DecisionQuerySet.as_manager()

    class Meta:
        ordering = ["-updated_at", "title", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(title=""),
                name="decision_title_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "draft",
                        "framing",
                        "open_for_contribution",
                        "under_review",
                        "ready_for_decision",
                        "decision_finalised",
                        "commitment",
                        "implementation",
                        "outcome_review",
                        "lessons_learned",
                        "archived",
                    ]
                ),
                name="decision_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(urgency__in=["low", "normal", "high", "critical"]),
                name="decision_urgency_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-updated_at"],
                name="decision_org_status_idx",
            ),
            models.Index(
                fields=["workspace", "status", "-updated_at"],
                name="decision_workspace_status_idx",
            ),
            models.Index(
                fields=["owner", "status", "-updated_at"],
                name="decision_owner_status_idx",
            ),
        ]

    def clean(self) -> None:
        """Normalise text and protect direct tenant ownership."""
        super().clean()
        self.title = self.title.strip()
        self.decision_question = self.decision_question.strip()
        self.purpose = self.purpose.strip()
        self.context = self.context.strip()
        self.scope = self.scope.strip()
        self.contribution_guidance = self.contribution_guidance.strip()
        self.source_template_key = self.source_template_key.strip()
        if self.source_template_key:
            from .templates import template_for_key

            template = template_for_key(self.source_template_key)
            if template is None:
                raise ValidationError(
                    {"source_template_key": "Use a recognised decision template."}
                )
            if self.source_template_version != template.version:
                raise ValidationError(
                    {
                        "source_template_version": (
                            "The template version must match the selected template."
                        )
                    }
                )
        elif self.source_template_version is not None:
            raise ValidationError(
                {"source_template_version": ("A template version requires a template key.")}
            )
        if self.source_method_version_id:
            if self.source_template_key:
                raise ValidationError(
                    {
                        "source_method_version": "Choose either a built-in template or an organisation method."
                    }
                )
            if self.source_method_version.organisation_id != self.organisation_id:
                raise ValidationError(
                    {
                        "source_method_version": "The method must belong to the decision organisation."
                    }
                )
            if self.source_method_version.status != "approved":
                raise ValidationError(
                    {"source_method_version": "Only an approved method version can be applied."}
                )
        if self.workspace_id and self.organisation_id:
            if self.workspace.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"workspace": "The workspace must belong to the decision organisation."}
                )

    def __str__(self) -> str:
        return self.title


class DecisionTransitionQuerySet(models.QuerySet["DecisionTransition"]):
    """Prevent mutation of lifecycle history."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Decision transitions are immutable.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Decision transitions are immutable.")


class DecisionTransition(UUIDTimeStampedModel):
    """An immutable human-authorised lifecycle state change."""

    decision = models.ForeignKey(
        Decision,
        on_delete=models.PROTECT,
        related_name="transitions",
    )
    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="decision_transitions",
    )
    sequence = models.PositiveIntegerField()
    from_status = models.CharField(max_length=40, choices=Decision.Status.choices)
    to_status = models.CharField(max_length=40, choices=Decision.Status.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="decision_transitions",
    )
    rationale = models.TextField(blank=True)
    warnings_acknowledged = models.JSONField(default=list, blank=True)

    objects = DecisionTransitionQuerySet.as_manager()

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "sequence"],
                name="unique_transition_sequence_per_decision",
            ),
            models.CheckConstraint(
                condition=~models.Q(from_status=models.F("to_status")),
                name="decision_transition_changes_status",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "-created_at"],
                name="transition_org_created_idx",
            )
        ]

    def clean(self) -> None:
        """Protect direct tenant ownership for lifecycle history."""
        super().clean()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The transition must share the decision organisation."}
                )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding is False:
            raise ValidationError("Decision transitions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Decision transitions are immutable.")

    def __str__(self) -> str:
        return f"{self.decision}: {self.from_status} → {self.to_status}"


class DecisionFinalisationQuerySet(models.QuerySet["DecisionFinalisation"]):
    """Prevent mutation of the human final decision record."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Decision finalisations are immutable.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Decision finalisations are immutable.")


class DecisionFinalisation(UUIDTimeStampedModel):
    """The immutable human-authored record that finalises a decision."""

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="decision_finalisations",
    )
    decision = models.OneToOneField(
        Decision,
        on_delete=models.PROTECT,
        related_name="finalisation",
    )
    selected_option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="finalisations",
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="finalised_decisions",
    )
    rationale = models.TextField()
    conditions = models.TextField(blank=True)
    dissent_summary = models.TextField(blank=True)
    position_snapshot = models.JSONField(default=list)
    decided_at = models.DateTimeField(default=timezone.now)

    objects = DecisionFinalisationQuerySet.as_manager()

    class Meta:
        ordering = ["-decided_at", "id"]
        indexes = [
            models.Index(
                fields=["organisation", "-decided_at"],
                name="finalisation_org_date_idx",
            ),
            models.Index(
                fields=["selected_option", "-decided_at"],
                name="finalisation_option_idx",
            ),
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(rationale=""),
                name="finalisation_rationale_not_empty",
            ),
        ]

    def clean(self) -> None:
        """Normalise text and enforce tenant-safe finalisation links."""
        super().clean()
        self.rationale = self.rationale.strip()
        self.conditions = self.conditions.strip()
        self.dissent_summary = self.dissent_summary.strip()
        errors: dict[str, str] = {}
        if not self.rationale:
            errors["rationale"] = "A final decision rationale is required."
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                errors["organisation"] = "The finalisation must share the decision organisation."
        if self.selected_option_id and self.decision_id:
            if self.selected_option.decision_id != self.decision_id:
                errors["selected_option"] = "The selected option must belong to this decision."
            if self.selected_option.organisation_id != self.organisation_id:
                errors["selected_option"] = "The selected option must share the organisation."
        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding is False:
            raise ValidationError("Decision finalisations are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Decision finalisations are immutable.")

    def __str__(self) -> str:
        return f"{self.decision.title}: {self.selected_option.title}"
