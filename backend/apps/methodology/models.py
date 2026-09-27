"""Organisation-owned, versioned decision methodologies."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class DecisionMethod(UUIDTimeStampedModel):
    """Stable organisation-owned identity for a governed decision method."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        RETIRED = "retired", "Retired"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="decision_methods"
    )
    key = models.SlugField(max_length=80)
    name = models.CharField(max_length=200)
    summary = models.TextField()
    best_for = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    current_version = models.ForeignKey(
        "DecisionMethodVersion",
        on_delete=models.PROTECT,
        related_name="current_for_methods",
        null=True,
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_decision_methods"
    )
    retired_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "key"], name="unique_method_key_per_org"
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "approved", "retired"]),
                name="decision_method_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""), name="decision_method_name_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(summary=""), name="decision_method_summary_not_empty"
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "status", "name"], name="method_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.key = self.key.strip().lower()
        self.name = self.name.strip()
        self.summary = self.summary.strip()
        self.best_for = self.best_for.strip()
        if self.current_version_id:
            if self.current_version.method_id != self.id:
                raise ValidationError(
                    {"current_version": "The current version must belong to this method."}
                )
            allowed_current_statuses: set[str] = (
                {str(DecisionMethodVersion.Status.APPROVED)}
                if self.status == self.Status.APPROVED
                else {
                    str(DecisionMethodVersion.Status.APPROVED),
                    str(DecisionMethodVersion.Status.RETIRED),
                }
            )
            if self.current_version.status not in allowed_current_statuses:
                raise ValidationError(
                    {
                        "current_version": "The current version must be an approved or retired governed version."
                    }
                )
        if self.status == self.Status.APPROVED and not self.current_version_id:
            raise ValidationError(
                {"current_version": "Approved methods require a current version."}
            )

    def __str__(self) -> str:
        return self.name


class DecisionMethodVersion(UUIDTimeStampedModel):
    """Immutable-after-approval prompt and process expectations for one method."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        APPROVED = "approved", "Approved"
        RETIRED = "retired", "Retired"

    method = models.ForeignKey(DecisionMethod, on_delete=models.CASCADE, related_name="versions")
    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="decision_method_versions",
    )
    version = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    question_prompt = models.TextField()
    purpose_prompt = models.TextField()
    context_prompt = models.TextField()
    scope_prompt = models.TextField()
    contribution_prompt = models.TextField()
    suggested_urgency = models.CharField(
        max_length=20,
        choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")],
        default="normal",
    )
    required_fields = models.JSONField(default=list, blank=True)
    checklist = models.JSONField(default=list, blank=True)
    evidence_prompts = models.JSONField(default=list, blank=True)
    assumption_prompts = models.JSONField(default=list, blank=True)
    risk_prompts = models.JSONField(default=list, blank=True)
    stakeholder_prompts = models.JSONField(default=list, blank=True)
    lifecycle_expectations = models.JSONField(default=list, blank=True)
    cloned_from_builtin_key = models.CharField(max_length=80, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_decision_method_versions",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="approved_decision_method_versions",
        null=True,
        blank=True,
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["method__name", "-version", "id"]
        constraints = [
            models.UniqueConstraint(fields=["method", "version"], name="unique_version_per_method"),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "approved", "retired"]),
                name="decision_method_version_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(suggested_urgency__in=["low", "normal", "high", "critical"]),
                name="decision_method_urgency_valid",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "status", "-version"], name="method_ver_org_status_idx"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        for field in (
            "question_prompt",
            "purpose_prompt",
            "context_prompt",
            "scope_prompt",
            "contribution_prompt",
        ):
            value = getattr(self, field).strip()
            setattr(self, field, value)
            if not value:
                raise ValidationError({field: "This prompt cannot be empty."})
        if (
            self.method_id
            and self.organisation_id
            and self.method.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The version must share the method organisation."}
            )
        allowed_fields = {
            "decision_question",
            "purpose",
            "context",
            "scope",
            "contribution_guidance",
        }
        if not isinstance(self.required_fields, list) or not set(self.required_fields).issubset(
            allowed_fields
        ):
            raise ValidationError({"required_fields": "Choose only supported framing fields."})
        for field in (
            "checklist",
            "evidence_prompts",
            "assumption_prompts",
            "risk_prompts",
            "stakeholder_prompts",
            "lifecycle_expectations",
        ):
            value = getattr(self, field)
            if not isinstance(value, list) or any(
                not isinstance(item, str) or not item.strip() for item in value
            ):
                raise ValidationError({field: "Provide a list of non-empty text prompts."})
        if self.status in {self.Status.APPROVED, self.Status.RETIRED} and (
            not self.approved_by_id or not self.approved_at
        ):
            raise ValidationError(
                {
                    "approved_by": "Approved and retired versions require preserved human approval attribution."
                }
            )
        if self.status == self.Status.DRAFT and (self.approved_by_id or self.approved_at):
            raise ValidationError(
                {"approved_by": "Draft versions cannot contain approval attribution."}
            )

    def __str__(self) -> str:
        return f"{self.method.name} v{self.version}"


class DecisionMethodUsage(UUIDTimeStampedModel):
    """Immutable record that a decision began from one approved method version."""

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="decision_method_usages",
    )
    method_version = models.ForeignKey(
        DecisionMethodVersion, on_delete=models.PROTECT, related_name="usages"
    )
    decision = models.OneToOneField(
        "decisions.Decision", on_delete=models.PROTECT, related_name="method_usage"
    )
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="applied_decision_methods"
    )

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["organisation", "-created_at"], name="method_usage_org_idx")
        ]

    def clean(self) -> None:
        super().clean()
        if self.method_version_id and self.organisation_id:
            if self.method_version.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The usage must share the method organisation."}
                )
            if self.method_version.status != DecisionMethodVersion.Status.APPROVED:
                raise ValidationError(
                    {"method_version": "Only approved method versions can be applied."}
                )
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError({"decision": "The decision must share the method organisation."})
