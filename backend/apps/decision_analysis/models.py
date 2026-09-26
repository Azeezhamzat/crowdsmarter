"""Governed issues, quality reviews, and executive synthesis for one decision."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class DecisionIssue(UUIDTimeStampedModel):
    """A human-accepted contradiction, gap, or blocker in the decision record."""

    class IssueType(models.TextChoices):
        EVIDENCE_CONTRADICTION = "evidence_contradiction", "Evidence contradiction"
        MISSING_EVIDENCE = "missing_evidence", "Missing evidence"
        UNSUPPORTED_ASSUMPTION = "unsupported_assumption", "Unsupported assumption"
        STAKEHOLDER_GAP = "stakeholder_gap", "Stakeholder gap"
        UNRESOLVED_OBJECTION = "unresolved_objection", "Unresolved objection"
        SCENARIO_VULNERABILITY = "scenario_vulnerability", "Scenario vulnerability"
        RESOURCE_UNCERTAINTY = "resource_uncertainty", "Resource uncertainty"
        IMPLEMENTATION_UNCERTAINTY = "implementation_uncertainty", "Implementation uncertainty"
        OTHER = "other", "Other"

    class Severity(models.TextChoices):
        LOW = "low", "Low"
        MODERATE = "moderate", "Moderate"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decision_analysis_issues",
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="analysis_issues"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    evidence = models.ForeignKey(
        "evidence.Evidence",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    assumption = models.ForeignKey(
        "assumptions.Assumption",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    risk = models.ForeignKey(
        "risks.Risk",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    evaluation_exercise = models.ForeignKey(
        "evaluations.EvaluationExercise",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    scenario_set = models.ForeignKey(
        "foresight.ScenarioSet",
        on_delete=models.PROTECT,
        related_name="analysis_issues",
        null=True,
        blank=True,
    )
    issue_type = models.CharField(max_length=40, choices=IssueType.choices)
    title = models.CharField(max_length=240)
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=Severity.choices, default=Severity.MODERATE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_decision_analysis_issues",
    )
    due_date = models.DateField(null=True, blank=True)
    resolution = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resolved_decision_analysis_issues",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decision_analysis_issues",
    )

    class Meta:
        ordering = ["status", "due_date", "created_at"]
        indexes = [
            models.Index(
                fields=["decision", "status", "severity"], name="analysis_issue_decision_idx"
            ),
            models.Index(fields=["organisation", "status"], name="analysis_issue_org_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.resolution = self.resolution.strip()
        if not self.title or not self.description:
            raise ValidationError("An issue requires a title and description.")
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The issue must share the decision organisation."}
            )
        for field_name in ("option", "evidence", "assumption", "risk"):
            value = getattr(self, field_name, None)
            if value is not None and value.decision_id != self.decision_id:
                raise ValidationError(
                    {field_name: "The linked record must belong to this decision."}
                )
        if self.evaluation_exercise_id and self.evaluation_exercise.decision_id != self.decision_id:
            raise ValidationError(
                {"evaluation_exercise": "The evaluation must belong to this decision."}
            )
        if self.scenario_set_id and self.scenario_set.linked_decision_id != self.decision_id:
            raise ValidationError(
                {"scenario_set": "The scenario set must be linked to this decision."}
            )
        if (
            self.owner_id
            and not self.organisation.memberships.filter(
                user_id=self.owner_id, status="active"
            ).exists()
        ):
            raise ValidationError({"owner": "The owner must be an active organisation member."})
        if self.status == self.Status.RESOLVED:
            if not self.resolution:
                raise ValidationError({"resolution": "Record how the issue was resolved."})
            if not self.resolved_at or not self.resolved_by_id:
                raise ValidationError("Resolved issues require resolution attribution.")
        elif self.resolved_at or self.resolved_by_id:
            raise ValidationError("Only resolved issues may contain resolution attribution.")


class DecisionQualityReview(UUIDTimeStampedModel):
    """A versioned, human-authored judgement of decision-process quality."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        SUPERSEDED = "superseded", "Superseded"

    class Judgement(models.TextChoices):
        NOT_READY = "not_ready", "Not ready"
        READY_WITH_CONDITIONS = "ready_with_conditions", "Ready with conditions"
        READY = "ready", "Ready"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decision_quality_reviews",
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="quality_reviews"
    )
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    judgement = models.CharField(
        max_length=30, choices=Judgement.choices, default=Judgement.NOT_READY
    )
    answers = models.JSONField(default=dict, blank=True)
    strengths = models.TextField(blank=True)
    blockers = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="authored_decision_quality_reviews",
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "version"], name="unique_quality_review_version"
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="draft"),
                name="one_draft_quality_review",
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="published"),
                name="one_published_quality_review",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="quality_review_version_positive"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.strengths = self.strengths.strip()
        self.blockers = self.blockers.strip()
        self.conditions = self.conditions.strip()
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The review must share the decision organisation."}
            )
        if self.status == self.Status.PUBLISHED and self.published_at is None:
            self.published_at = timezone.now()
        if self.judgement == self.Judgement.READY_WITH_CONDITIONS and not self.conditions:
            raise ValidationError({"conditions": "Record the conditions attached to readiness."})


class ExecutiveDecisionSummary(UUIDTimeStampedModel):
    """A versioned, human-approved executive synthesis of the decision record."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        SUPERSEDED = "superseded", "Superseded"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="executive_decision_summaries",
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="executive_summaries"
    )
    version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    context_summary = models.TextField(blank=True)
    options_summary = models.TextField(blank=True)
    evidence_summary = models.TextField(blank=True)
    uncertainty_summary = models.TextField(blank=True)
    stakeholder_summary = models.TextField(blank=True)
    scenario_summary = models.TextField(blank=True)
    evaluation_summary = models.TextField(blank=True)
    risk_summary = models.TextField(blank=True)
    unresolved_issues = models.TextField(blank=True)
    proposed_judgement = models.TextField(blank=True)
    conditions = models.TextField(blank=True)
    implementation_implications = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_executive_decision_summaries",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_executive_decision_summaries",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-version", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["decision", "version"], name="unique_executive_summary_version"
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="draft"),
                name="one_draft_executive_summary",
            ),
            models.UniqueConstraint(
                fields=["decision"],
                condition=models.Q(status="approved"),
                name="one_approved_executive_summary",
            ),
            models.CheckConstraint(
                condition=models.Q(version__gte=1), name="executive_summary_version_positive"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        for field_name in (
            "context_summary",
            "options_summary",
            "evidence_summary",
            "uncertainty_summary",
            "stakeholder_summary",
            "scenario_summary",
            "evaluation_summary",
            "risk_summary",
            "unresolved_issues",
            "proposed_judgement",
            "conditions",
            "implementation_implications",
        ):
            setattr(self, field_name, getattr(self, field_name).strip())
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The summary must share the decision organisation."}
            )
        if self.status == self.Status.APPROVED:
            if not self.proposed_judgement:
                raise ValidationError(
                    {"proposed_judgement": "An approved summary requires a proposed judgement."}
                )
            if not self.approved_by_id or not self.approved_at:
                raise ValidationError("Approved summaries require human approval attribution.")
        elif self.status == self.Status.DRAFT and (self.approved_by_id or self.approved_at):
            raise ValidationError("Draft summaries cannot contain approval attribution.")
        elif self.status == self.Status.SUPERSEDED and (
            not self.approved_by_id or not self.approved_at
        ):
            raise ValidationError(
                "Superseded summaries must preserve their original approval attribution."
            )
