"""Governed contribution assignments, submissions, reviews, and facilitation."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class FacilitationSession(UUIDTimeStampedModel):
    """A bounded, attributable workshop attached to one decision."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="facilitation_sessions"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="facilitation_sessions"
    )
    title = models.CharField(max_length=240)
    objective = models.TextField()
    agenda = models.TextField(blank=True)
    participation_guidance = models.TextField(blank=True)
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="facilitated_sessions"
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_facilitation_sessions"
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["starts_at", "created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["planned", "open", "closed", "cancelled"]),
                name="facilitation_session_status_valid",
            ),
            models.CheckConstraint(condition=~models.Q(title=""), name="facilitation_session_title_not_empty"),
            models.CheckConstraint(condition=~models.Q(objective=""), name="facilitation_session_objective_not_empty"),
        ]
        indexes = [
            models.Index(fields=["decision", "status", "starts_at"], name="fac_session_decision_idx"),
            models.Index(fields=["organisation", "facilitator", "status"], name="fac_session_facilitator_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.objective = self.objective.strip()
        self.agenda = self.agenda.strip()
        self.participation_guidance = self.participation_guidance.strip()
        if self.decision_id and self.organisation_id and self.decision.organisation_id != self.organisation_id:
            raise ValidationError({"organisation": "The session must share the decision organisation."})
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "The end time must be later than the start time."})
        if self.status == self.Status.CLOSED and not self.closed_at:
            raise ValidationError({"closed_at": "Closed sessions require a closure timestamp."})
        if self.status != self.Status.CLOSED and self.closed_at:
            raise ValidationError({"closed_at": "Only closed sessions may contain a closure timestamp."})

    def __str__(self) -> str:
        return f"{self.title} - {self.decision}"


class SessionParticipant(UUIDTimeStampedModel):
    """An invited organisation member and their workshop attendance state."""

    class Role(models.TextChoices):
        PARTICIPANT = "participant", "Participant"
        OBSERVER = "observer", "Observer"

    class Attendance(models.TextChoices):
        INVITED = "invited", "Invited"
        ATTENDED = "attended", "Attended"
        ABSENT = "absent", "Absent"

    session = models.ForeignKey(FacilitationSession, on_delete=models.CASCADE, related_name="participants")
    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="facilitation_participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="facilitation_participations"
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    attendance = models.CharField(max_length=20, choices=Attendance.choices, default=Attendance.INVITED)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="added_facilitation_participants"
    )

    class Meta:
        ordering = ["role", "user__email", "id"]
        constraints = [
            models.UniqueConstraint(fields=["session", "user"], name="one_user_per_facilitation_session"),
            models.CheckConstraint(
                condition=models.Q(role__in=["participant", "observer"]),
                name="session_participant_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(attendance__in=["invited", "attended", "absent"]),
                name="session_participant_attendance_valid",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        if self.session_id and self.organisation_id and self.session.organisation_id != self.organisation_id:
            raise ValidationError({"organisation": "The participant must share the session organisation."})


class ContributionRequest(UUIDTimeStampedModel):
    """A named request for a bounded contribution from one decision participant."""

    class Kind(models.TextChoices):
        EVIDENCE = "evidence", "Evidence"
        ASSUMPTION = "assumption", "Assumption"
        RISK = "risk", "Risk"
        STAKEHOLDER = "stakeholder", "Stakeholder perspective"
        OPTION = "option", "Option"
        QUESTION = "question", "Question response"
        REVIEW = "review", "Review"
        SCENARIO = "scenario", "Scenario contribution"
        IMPLEMENTATION = "implementation", "Implementation input"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        ACCEPTED = "accepted", "Accepted"
        RETURNED = "returned", "Returned"
        CANCELLED = "cancelled", "Cancelled"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        CRITICAL = "critical", "Critical"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="contribution_requests"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="contribution_requests"
    )
    option = models.ForeignKey(
        "decision_options.DecisionOption", on_delete=models.PROTECT, related_name="contribution_requests",
        null=True, blank=True,
    )
    session = models.ForeignKey(
        FacilitationSession, on_delete=models.PROTECT, related_name="contribution_requests",
        null=True, blank=True,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_contributions"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_contributions"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="reviewed_contribution_requests",
        null=True, blank=True,
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    title = models.CharField(max_length=240)
    instructions = models.TextField()
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    due_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["due_at", "-priority", "created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=[
                    "evidence", "assumption", "risk", "stakeholder", "option", "question",
                    "review", "scenario", "implementation", "other",
                ]),
                name="contribution_request_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=[
                    "draft", "open", "in_progress", "submitted", "under_review",
                    "accepted", "returned", "cancelled",
                ]),
                name="contribution_request_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=["low", "normal", "high", "critical"]),
                name="contribution_request_priority_valid",
            ),
            models.CheckConstraint(condition=~models.Q(title=""), name="contribution_request_title_not_empty"),
            models.CheckConstraint(condition=~models.Q(instructions=""), name="contribution_request_instructions_not_empty"),
        ]
        indexes = [
            models.Index(fields=["decision", "status", "due_at"], name="contribution_decision_idx"),
            models.Index(fields=["assignee", "status", "due_at"], name="contribution_assignee_idx"),
            models.Index(fields=["organisation", "status", "priority"], name="contribution_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.instructions = self.instructions.strip()
        if self.decision_id and self.organisation_id and self.decision.organisation_id != self.organisation_id:
            raise ValidationError({"organisation": "The request must share the decision organisation."})
        if self.option_id and self.option.decision_id != self.decision_id:
            raise ValidationError({"option": "The option must belong to this decision."})
        if self.session_id and self.session.decision_id != self.decision_id:
            raise ValidationError({"session": "The facilitation session must belong to this decision."})
        if self.reviewer_id and self.reviewer_id == self.assignee_id:
            raise ValidationError({"reviewer": "The reviewer must be different from the assignee."})

    @property
    def is_terminal(self) -> bool:
        return self.status in {self.Status.ACCEPTED, self.Status.CANCELLED}

    def __str__(self) -> str:
        return f"{self.title} - {self.assignee}"


class ContributionSubmission(UUIDTimeStampedModel):
    """A saved draft or immutable submitted revision for one contribution request."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="contribution_submissions"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="contribution_submissions"
    )
    request = models.ForeignKey(ContributionRequest, on_delete=models.CASCADE, related_name="submissions")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contribution_submissions"
    )
    sequence = models.PositiveIntegerField()
    body = models.TextField()
    references = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["request", "sequence", "id"]
        constraints = [
            models.UniqueConstraint(fields=["request", "sequence"], name="contribution_submission_sequence_unique"),
            models.UniqueConstraint(
                fields=["request", "author"], condition=models.Q(status="draft"),
                name="one_contribution_draft_per_author",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "submitted"]),
                name="contribution_submission_status_valid",
            ),
            models.CheckConstraint(condition=~models.Q(body=""), name="contribution_submission_body_not_empty"),
        ]
        indexes = [
            models.Index(fields=["request", "status", "-sequence"], name="contribution_submission_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()
        self.references = self.references.strip()
        if self.request_id:
            if self.request.organisation_id != self.organisation_id or self.request.decision_id != self.decision_id:
                raise ValidationError("The submission must share its request tenant and decision.")
            if self.author_id != self.request.assignee_id:
                raise ValidationError({"author": "Only the assigned contributor may author the submission."})
        if self.status == self.Status.SUBMITTED and not self.submitted_at:
            raise ValidationError({"submitted_at": "Submitted revisions require a timestamp."})
        if self.status == self.Status.DRAFT and self.submitted_at:
            raise ValidationError({"submitted_at": "Draft revisions cannot contain a submission timestamp."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            original = ContributionSubmission.objects.get(pk=self.pk)
            if original.status == self.Status.SUBMITTED:
                raise ValidationError("Submitted contribution revisions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        if self.status == self.Status.SUBMITTED:
            raise ValidationError("Submitted contribution revisions cannot be deleted.")
        return super().delete(*args, **kwargs)


class ContributionReview(UUIDTimeStampedModel):
    """An append-only acceptance, return, or review note for a submitted revision."""

    class Outcome(models.TextChoices):
        ACCEPTED = "accepted", "Accepted"
        RETURNED = "returned", "Returned"
        COMMENT = "comment", "Comment"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="contribution_reviews"
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="contribution_reviews"
    )
    request = models.ForeignKey(ContributionRequest, on_delete=models.CASCADE, related_name="reviews")
    submission = models.ForeignKey(ContributionSubmission, on_delete=models.PROTECT, related_name="reviews")
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="contribution_reviews"
    )
    outcome = models.CharField(max_length=20, choices=Outcome.choices)
    note = models.TextField()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(outcome__in=["accepted", "returned", "comment"]),
                name="contribution_review_outcome_valid",
            ),
            models.CheckConstraint(condition=~models.Q(note=""), name="contribution_review_note_not_empty"),
        ]

    def clean(self) -> None:
        super().clean()
        self.note = self.note.strip()
        if self.request_id and self.submission_id and self.submission.request_id != self.request_id:
            raise ValidationError({"submission": "The reviewed submission must belong to this request."})
        if self.request_id and (
            self.request.organisation_id != self.organisation_id or self.request.decision_id != self.decision_id
        ):
            raise ValidationError("The review must share its request tenant and decision.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Contribution reviews are append-only.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Contribution reviews are append-only.")


class ContributionPreference(UUIDTimeStampedModel):
    """Per-organisation delivery preferences for contribution reminders and digests."""

    class DigestCadence(models.TextChoices):
        IMMEDIATE = "immediate", "Immediate"
        DAILY = "daily", "Daily digest"
        WEEKLY = "weekly", "Weekly digest"
        NONE = "none", "No email digest"

    organisation = models.ForeignKey(
        "organisations.Organisation", on_delete=models.CASCADE, related_name="contribution_preferences"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="contribution_preferences"
    )
    digest_cadence = models.CharField(
        max_length=20, choices=DigestCadence.choices, default=DigestCadence.DAILY
    )
    email_enabled = models.BooleanField(default=False)
    due_reminders_enabled = models.BooleanField(default=True)
    reminder_days_before = models.PositiveSmallIntegerField(default=2)
    last_digest_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["organisation", "user__email"]
        constraints = [
            models.UniqueConstraint(fields=["organisation", "user"], name="one_contribution_preference_per_org_user"),
            models.CheckConstraint(
                condition=models.Q(digest_cadence__in=["immediate", "daily", "weekly", "none"]),
                name="contribution_digest_cadence_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(reminder_days_before__gte=0, reminder_days_before__lte=30),
                name="contribution_reminder_days_range",
            ),
        ]
