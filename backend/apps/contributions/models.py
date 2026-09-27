"""Governed contribution assignments, submissions, reviews, and facilitation."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.core.models import UUIDTimeStampedModel


class FacilitationSession(UUIDTimeStampedModel):
    """A bounded, attributable workshop attached to one decision."""

    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        CANCELLED = "cancelled", "Cancelled"

    class Channel(models.TextChoices):
        IN_PERSON = "in_person", "In person"
        PHONE = "phone", "Telephone"
        PAPER = "paper", "Paper"
        PARTNER_ASSISTED = "partner_assisted", "Partner assisted"
        DIGITAL = "digital", "Digital"
        OTHER = "other", "Other"

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
    influence_boundary = models.TextField(blank=True)
    fixed_constraints = models.TextField(blank=True)
    participation_channels = models.JSONField(default=list, blank=True)
    missing_perspectives = models.TextField(blank=True)
    accessibility_arrangements = models.TextField(blank=True)
    consent_boundary = models.TextField(blank=True)
    facilitator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="facilitated_sessions"
    )
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PLANNED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_facilitation_sessions",
    )
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["starts_at", "created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["planned", "open", "closed", "cancelled"]),
                name="facilitation_session_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(title=""), name="facilitation_session_title_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(objective=""), name="facilitation_session_objective_not_empty"
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "status", "starts_at"], name="fac_session_decision_idx"
            ),
            models.Index(
                fields=["organisation", "facilitator", "status"], name="fac_session_facilitator_idx"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.objective = self.objective.strip()
        self.agenda = self.agenda.strip()
        self.participation_guidance = self.participation_guidance.strip()
        self.influence_boundary = self.influence_boundary.strip()
        self.fixed_constraints = self.fixed_constraints.strip()
        self.missing_perspectives = self.missing_perspectives.strip()
        self.accessibility_arrangements = self.accessibility_arrangements.strip()
        self.consent_boundary = self.consent_boundary.strip()
        if not isinstance(self.participation_channels, list) or any(
            not isinstance(channel, str) or channel not in self.Channel.values
            for channel in self.participation_channels
        ):
            raise ValidationError(
                {"participation_channels": "Select only supported participation channels."}
            )
        if len(self.participation_channels) != len(set(self.participation_channels)):
            raise ValidationError(
                {"participation_channels": "Each participation channel may appear only once."}
            )
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The session must share the decision organisation."}
            )
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "The end time must be later than the start time."})
        if self.status == self.Status.CLOSED and not self.closed_at:
            raise ValidationError({"closed_at": "Closed sessions require a closure timestamp."})
        if self.status != self.Status.CLOSED and self.closed_at:
            raise ValidationError(
                {"closed_at": "Only closed sessions may contain a closure timestamp."}
            )

    def __str__(self) -> str:
        return f"{self.title} - {self.decision}"


class FacilitationAgendaItem(UUIDTimeStampedModel):
    """A timed, actionable step in a facilitation run-of-show."""

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"

    session = models.ForeignKey(
        FacilitationSession, on_delete=models.CASCADE, related_name="agenda_items"
    )
    title = models.CharField(max_length=240)
    purpose = models.TextField(blank=True)
    method = models.CharField(max_length=240, blank=True)
    facilitator_prompt = models.TextField(blank=True)
    output_prompt = models.TextField(blank=True)
    planned_minutes = models.PositiveSmallIntegerField(default=10)
    order = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_facilitation_agenda_items",
    )

    class Meta:
        ordering = ["order", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "order"], name="one_facilitation_agenda_order"
            ),
            models.UniqueConstraint(
                fields=["session"],
                condition=models.Q(status="active"),
                name="one_active_facilitation_agenda_item",
            ),
            models.CheckConstraint(
                condition=~models.Q(title=""), name="facilitation_agenda_title_not_empty"
            ),
            models.CheckConstraint(
                condition=models.Q(planned_minutes__gte=1, planned_minutes__lte=480),
                name="facilitation_agenda_minutes_range",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["queued", "active", "completed", "skipped"]),
                name="facilitation_agenda_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["session", "status", "order"], name="fac_agenda_session_idx")
        ]

    @property
    def actual_minutes(self) -> float | None:
        if not self.started_at:
            return None
        end = self.ended_at or timezone.now()
        return round(max(0, (end - self.started_at).total_seconds()) / 60, 1)

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.purpose = self.purpose.strip()
        self.method = self.method.strip()
        self.facilitator_prompt = self.facilitator_prompt.strip()
        self.output_prompt = self.output_prompt.strip()
        if self.status == self.Status.QUEUED and (self.started_at or self.ended_at):
            raise ValidationError(
                {"status": "Queued agenda items cannot contain execution timestamps."}
            )
        if self.status == self.Status.ACTIVE and (not self.started_at or self.ended_at):
            raise ValidationError(
                {"status": "Active agenda items require a start and cannot have an end."}
            )
        if self.status == self.Status.COMPLETED and (not self.started_at or not self.ended_at):
            raise ValidationError(
                {"status": "Completed agenda items require start and end timestamps."}
            )
        if self.ended_at and self.started_at and self.ended_at < self.started_at:
            raise ValidationError({"ended_at": "The end cannot precede the start."})

    def __str__(self) -> str:
        return f"{self.order}. {self.title}"


class SessionParticipant(UUIDTimeStampedModel):
    """An invited organisation member and their workshop attendance state."""

    class Role(models.TextChoices):
        PARTICIPANT = "participant", "Participant"
        OBSERVER = "observer", "Observer"

    class Attendance(models.TextChoices):
        INVITED = "invited", "Invited"
        ATTENDED = "attended", "Attended"
        ABSENT = "absent", "Absent"

    session = models.ForeignKey(
        FacilitationSession, on_delete=models.CASCADE, related_name="participants"
    )
    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="facilitation_participants",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="facilitation_participations",
        null=True,
        blank=True,
    )
    external_label = models.CharField(max_length=240, blank=True)
    stakeholder_group = models.CharField(max_length=240, blank=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARTICIPANT)
    attendance = models.CharField(
        max_length=20, choices=Attendance.choices, default=Attendance.INVITED
    )
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="added_facilitation_participants",
    )

    class Meta:
        ordering = ["role", "user__email", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "user"], name="one_user_per_facilitation_session"
            ),
            models.CheckConstraint(
                condition=models.Q(role__in=["participant", "observer"]),
                name="session_participant_role_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(attendance__in=["invited", "attended", "absent"]),
                name="session_participant_attendance_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(user__isnull=False) | ~models.Q(external_label=""),
                name="session_participant_identity_present",
            ),
            models.UniqueConstraint(
                fields=["session", "external_label"],
                condition=~models.Q(external_label=""),
                name="one_external_label_per_session",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.external_label = self.external_label.strip()
        self.stakeholder_group = self.stakeholder_group.strip()
        if (
            self.session_id
            and self.organisation_id
            and self.session.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The participant must share the session organisation."}
            )
        if not self.user_id and not self.external_label:
            raise ValidationError(
                {"external_label": "Provide an organisation user or an offline participant label."}
            )
        if self.user_id and self.external_label:
            raise ValidationError(
                {"external_label": "Use either an organisation user or an offline label."}
            )

    @property
    def display_label(self) -> str:
        if self.user_id:
            return (
                " ".join(filter(None, [self.user.first_name, self.user.last_name]))
                or self.user.email
            )
        return self.external_label


class FacilitationRecord(UUIDTimeStampedModel):
    """An append-only, provenance-aware record captured during or after a session."""

    class Kind(models.TextChoices):
        AGREEMENT = "agreement", "Agreement"
        DISAGREEMENT = "disagreement", "Unresolved disagreement"
        ACTION = "action", "Action"
        EVIDENCE_GAP = "evidence_gap", "Evidence gap"
        NEXT_QUESTION = "next_question", "Next question"
        PARTICIPANT_STATEMENT = "participant_statement", "Participant statement"

    class Channel(models.TextChoices):
        IN_PERSON = "in_person", "In person"
        PHONE = "phone", "Telephone"
        PAPER = "paper", "Paper"
        PARTNER_ASSISTED = "partner_assisted", "Partner assisted"
        DIGITAL = "digital", "Digital"
        OTHER = "other", "Other"

    class Attribution(models.TextChoices):
        ATTRIBUTED = "attributed", "Attributed"
        ANONYMOUS = "anonymous", "Anonymous"
        CONFIDENTIAL = "confidential", "Confidential"

    class Origin(models.TextChoices):
        PARTICIPANT_INPUT = "participant_input", "Participant input"
        FACILITATOR_SYNTHESIS = "facilitator_synthesis", "Facilitator synthesis"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="facilitation_records",
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="facilitation_records"
    )
    session = models.ForeignKey(
        FacilitationSession, on_delete=models.CASCADE, related_name="records"
    )
    agenda_item = models.ForeignKey(
        FacilitationAgendaItem,
        on_delete=models.PROTECT,
        related_name="records",
        null=True,
        blank=True,
    )
    kind = models.CharField(max_length=30, choices=Kind.choices)
    body = models.TextField()
    channel = models.CharField(max_length=30, choices=Channel.choices)
    origin = models.CharField(max_length=30, choices=Origin.choices)
    attribution = models.CharField(
        max_length=20, choices=Attribution.choices, default=Attribution.ANONYMOUS
    )
    source_participant = models.ForeignKey(
        SessionParticipant,
        on_delete=models.PROTECT,
        related_name="facilitation_records",
        null=True,
        blank=True,
    )
    speaker_label = models.CharField(max_length=240, blank=True)
    permission_to_quote = models.BooleanField(default=False)
    follow_up_owner = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_facilitation_records",
    )

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(
                    kind__in=[
                        "agreement",
                        "disagreement",
                        "action",
                        "evidence_gap",
                        "next_question",
                        "participant_statement",
                    ]
                ),
                name="facilitation_record_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    channel__in=[
                        "in_person",
                        "phone",
                        "paper",
                        "partner_assisted",
                        "digital",
                        "other",
                    ]
                ),
                name="facilitation_record_channel_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(attribution__in=["attributed", "anonymous", "confidential"]),
                name="facilitation_attribution_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(origin__in=["participant_input", "facilitator_synthesis"]),
                name="facilitation_record_origin_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(body=""), name="facilitation_record_body_not_empty"
            ),
        ]
        indexes = [
            models.Index(fields=["session", "kind", "created_at"], name="fac_record_session_idx"),
            models.Index(fields=["decision", "channel"], name="fac_record_decision_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()
        self.speaker_label = self.speaker_label.strip()
        self.follow_up_owner = self.follow_up_owner.strip()
        if self.session_id and (
            self.session.organisation_id != self.organisation_id
            or self.session.decision_id != self.decision_id
        ):
            raise ValidationError("The record must share its session tenant and decision.")
        if self.source_participant_id and self.source_participant.session_id != self.session_id:
            raise ValidationError(
                {"source_participant": "The source participant must belong to this session."}
            )
        if self.agenda_item_id and self.agenda_item.session_id != self.session_id:
            raise ValidationError({"agenda_item": "The agenda item must belong to this session."})
        if self.attribution == self.Attribution.ANONYMOUS and (
            self.source_participant_id or self.speaker_label
        ):
            raise ValidationError(
                {"attribution": "Anonymous records cannot retain a participant identity."}
            )
        if (
            self.origin == self.Origin.PARTICIPANT_INPUT
            and self.attribution == self.Attribution.ATTRIBUTED
            and not (self.source_participant_id or self.speaker_label)
        ):
            raise ValidationError(
                {"speaker_label": "Attributed participant input requires a source identity."}
            )

    def __str__(self) -> str:
        return f"{self.get_kind_display()} - {self.session}"


class FacilitationAuthorityResponse(UUIDTimeStampedModel):
    """The accountable authority's explicit response that closes a session feedback loop."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="facilitation_authority_responses",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.CASCADE,
        related_name="facilitation_authority_responses",
    )
    session = models.OneToOneField(
        FacilitationSession, on_delete=models.CASCADE, related_name="authority_response"
    )
    what_we_heard = models.TextField(blank=True)
    what_changed = models.TextField(blank=True)
    what_did_not_change = models.TextField(blank=True)
    rationale = models.TextField(blank=True)
    next_steps = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    published_at = models.DateTimeField(null=True, blank=True)
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="published_facilitation_responses",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["session", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "published"]),
                name="facilitation_response_status_valid",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        for field in [
            "what_we_heard",
            "what_changed",
            "what_did_not_change",
            "rationale",
            "next_steps",
        ]:
            setattr(self, field, getattr(self, field).strip())
        if self.session_id and (
            self.session.organisation_id != self.organisation_id
            or self.session.decision_id != self.decision_id
        ):
            raise ValidationError("The response must share its session tenant and decision.")
        if self.status == self.Status.PUBLISHED:
            if not self.what_we_heard:
                raise ValidationError(
                    {"what_we_heard": "A published response must say what was heard."}
                )
            if not (self.what_changed or self.what_did_not_change):
                raise ValidationError(
                    {"what_changed": "Record what changed or what did not change."}
                )
            if self.what_did_not_change and not self.rationale:
                raise ValidationError(
                    {"rationale": "Explain why recorded input did not change the decision."}
                )
            if not self.next_steps:
                raise ValidationError(
                    {"next_steps": "A published response must state what happens next."}
                )
            if not self.published_at or not self.published_by_id:
                raise ValidationError("Published responses require an authority and timestamp.")
        elif self.published_at or self.published_by_id:
            raise ValidationError("Draft responses cannot contain publication details.")

    def __str__(self) -> str:
        return f"Authority response - {self.session}"


class FacilitationQualityReview(UUIDTimeStampedModel):
    """A facilitator's explicit post-session quality and learning assessment."""

    session = models.OneToOneField(
        FacilitationSession, on_delete=models.CASCADE, related_name="quality_review"
    )
    inclusion_score = models.PositiveSmallIntegerField()
    clarity_score = models.PositiveSmallIntegerField()
    neutrality_score = models.PositiveSmallIntegerField()
    participation_score = models.PositiveSmallIntegerField()
    follow_through_score = models.PositiveSmallIntegerField()
    what_worked = models.TextField()
    improve_next_time = models.TextField()
    unresolved_risks = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="facilitation_quality_reviews",
    )
    reviewed_at = models.DateTimeField()

    class Meta:
        ordering = ["-reviewed_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(inclusion_score__gte=1, inclusion_score__lte=5),
                name="fac_quality_inclusion_range",
            ),
            models.CheckConstraint(
                condition=models.Q(clarity_score__gte=1, clarity_score__lte=5),
                name="fac_quality_clarity_range",
            ),
            models.CheckConstraint(
                condition=models.Q(neutrality_score__gte=1, neutrality_score__lte=5),
                name="fac_quality_neutrality_range",
            ),
            models.CheckConstraint(
                condition=models.Q(participation_score__gte=1, participation_score__lte=5),
                name="fac_quality_participation_range",
            ),
            models.CheckConstraint(
                condition=models.Q(follow_through_score__gte=1, follow_through_score__lte=5),
                name="fac_quality_follow_through_range",
            ),
            models.CheckConstraint(
                condition=~models.Q(what_worked=""), name="fac_quality_what_worked_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(improve_next_time=""),
                name="fac_quality_improvement_not_empty",
            ),
        ]

    @property
    def overall_score(self) -> float:
        return round(
            (
                self.inclusion_score
                + self.clarity_score
                + self.neutrality_score
                + self.participation_score
                + self.follow_through_score
            )
            / 5,
            1,
        )

    def clean(self) -> None:
        super().clean()
        self.what_worked = self.what_worked.strip()
        self.improve_next_time = self.improve_next_time.strip()
        self.unresolved_risks = self.unresolved_risks.strip()

    def __str__(self) -> str:
        return f"Quality review - {self.session}"


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
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="contribution_requests",
        null=True,
        blank=True,
    )
    session = models.ForeignKey(
        FacilitationSession,
        on_delete=models.PROTECT,
        related_name="contribution_requests",
        null=True,
        blank=True,
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="requested_contributions"
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="assigned_contributions"
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="reviewed_contribution_requests",
        null=True,
        blank=True,
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
                condition=models.Q(
                    kind__in=[
                        "evidence",
                        "assumption",
                        "risk",
                        "stakeholder",
                        "option",
                        "question",
                        "review",
                        "scenario",
                        "implementation",
                        "other",
                    ]
                ),
                name="contribution_request_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        "draft",
                        "open",
                        "in_progress",
                        "submitted",
                        "under_review",
                        "accepted",
                        "returned",
                        "cancelled",
                    ]
                ),
                name="contribution_request_status_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(priority__in=["low", "normal", "high", "critical"]),
                name="contribution_request_priority_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(title=""), name="contribution_request_title_not_empty"
            ),
            models.CheckConstraint(
                condition=~models.Q(instructions=""),
                name="contribution_request_instructions_not_empty",
            ),
        ]
        indexes = [
            models.Index(fields=["decision", "status", "due_at"], name="contribution_decision_idx"),
            models.Index(fields=["assignee", "status", "due_at"], name="contribution_assignee_idx"),
            models.Index(
                fields=["organisation", "status", "priority"], name="contribution_org_status_idx"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.instructions = self.instructions.strip()
        if (
            self.decision_id
            and self.organisation_id
            and self.decision.organisation_id != self.organisation_id
        ):
            raise ValidationError(
                {"organisation": "The request must share the decision organisation."}
            )
        if self.option_id and self.option.decision_id != self.decision_id:
            raise ValidationError({"option": "The option must belong to this decision."})
        if self.session_id and self.session.decision_id != self.decision_id:
            raise ValidationError(
                {"session": "The facilitation session must belong to this decision."}
            )
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
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="contribution_submissions",
    )
    decision = models.ForeignKey(
        "decisions.Decision", on_delete=models.CASCADE, related_name="contribution_submissions"
    )
    request = models.ForeignKey(
        ContributionRequest, on_delete=models.CASCADE, related_name="submissions"
    )
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
            models.UniqueConstraint(
                fields=["request", "sequence"], name="contribution_submission_sequence_unique"
            ),
            models.UniqueConstraint(
                fields=["request", "author"],
                condition=models.Q(status="draft"),
                name="one_contribution_draft_per_author",
            ),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "submitted"]),
                name="contribution_submission_status_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(body=""), name="contribution_submission_body_not_empty"
            ),
        ]
        indexes = [
            models.Index(
                fields=["request", "status", "-sequence"], name="contribution_submission_idx"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()
        self.references = self.references.strip()
        if self.request_id:
            if (
                self.request.organisation_id != self.organisation_id
                or self.request.decision_id != self.decision_id
            ):
                raise ValidationError("The submission must share its request tenant and decision.")
            if self.author_id != self.request.assignee_id:
                raise ValidationError(
                    {"author": "Only the assigned contributor may author the submission."}
                )
        if self.status == self.Status.SUBMITTED and not self.submitted_at:
            raise ValidationError({"submitted_at": "Submitted revisions require a timestamp."})
        if self.status == self.Status.DRAFT and self.submitted_at:
            raise ValidationError(
                {"submitted_at": "Draft revisions cannot contain a submission timestamp."}
            )

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
    request = models.ForeignKey(
        ContributionRequest, on_delete=models.CASCADE, related_name="reviews"
    )
    submission = models.ForeignKey(
        ContributionSubmission, on_delete=models.PROTECT, related_name="reviews"
    )
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
            models.CheckConstraint(
                condition=~models.Q(note=""), name="contribution_review_note_not_empty"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.note = self.note.strip()
        if self.request_id and self.submission_id and self.submission.request_id != self.request_id:
            raise ValidationError(
                {"submission": "The reviewed submission must belong to this request."}
            )
        if self.request_id and (
            self.request.organisation_id != self.organisation_id
            or self.request.decision_id != self.decision_id
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
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="contribution_preferences",
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
            models.UniqueConstraint(
                fields=["organisation", "user"], name="one_contribution_preference_per_org_user"
            ),
            models.CheckConstraint(
                condition=models.Q(digest_cadence__in=["immediate", "daily", "weekly", "none"]),
                name="contribution_digest_cadence_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(reminder_days_before__gte=0, reminder_days_before__lte=30),
                name="contribution_reminder_days_range",
            ),
        ]
