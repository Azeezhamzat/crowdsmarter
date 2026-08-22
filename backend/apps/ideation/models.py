"""Lightweight, shareable idea collection and voting outside organisation membership."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class OpenSession(UUIDTimeStampedModel):
    """A prompt-driven, publicly shareable container for idea collection and voting.

    Standalone (decision is null) it serves ideathons and lightweight problem
    analysis; linked to a Decision it opens that one decision to outside input
    without adding external people as real Participants.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="open_sessions",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.PROTECT,
        related_name="open_sessions",
        null=True,
        blank=True,
    )
    default_workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.PROTECT,
        related_name="open_sessions",
        null=True,
        blank=True,
        help_text="Workspace used when auto-creating a Decision from a promoted idea.",
    )
    title = models.CharField(max_length=240)
    prompt = models.TextField()
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    public_slug = models.CharField(max_length=32, unique=True)
    voting_enabled = models.BooleanField(default=True)
    submission_deadline = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_open_sessions",
    )

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="open_session_title_not_empty"),
            models.CheckConstraint(condition=~models.Q(public_slug=""), name="open_session_slug_not_empty"),
            models.CheckConstraint(
                condition=models.Q(status__in=["draft", "open", "closed", "archived"]),
                name="open_session_status_valid",
            ),
        ]
        indexes = [
            models.Index(fields=["organisation", "status"], name="open_session_org_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.prompt = self.prompt.strip()
        self.description = self.description.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The session must share the linked decision's organisation."}
                )

    def __str__(self) -> str:
        return f"{self.organisation.name}: {self.title}"


class SessionParticipant(UUIDTimeStampedModel):
    """A lightweight, name-and-email identity for someone outside org membership."""

    session = models.ForeignKey(OpenSession, on_delete=models.CASCADE, related_name="participants")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    token_digest = models.CharField(max_length=64, unique=True)

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(name=""), name="session_participant_name_not_empty"),
            models.CheckConstraint(condition=~models.Q(email=""), name="session_participant_email_not_empty"),
            models.UniqueConstraint(
                fields=["session", "email"],
                name="unique_participant_per_session_email",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.name = self.name.strip()
        self.email = self.email.strip().lower()

    def __str__(self) -> str:
        return f"{self.name} <{self.email}> in {self.session.title}"


class Idea(UUIDTimeStampedModel):
    """One freeform submission to an OpenSession, from a participant or an org member."""

    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        SHORTLISTED = "shortlisted", "Shortlisted"
        PROMOTED = "promoted", "Promoted"
        ARCHIVED = "archived", "Archived"

    session = models.ForeignKey(OpenSession, on_delete=models.CASCADE, related_name="ideas")
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=60, blank=True)
    requested_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    submitted_by_participant = models.ForeignKey(
        SessionParticipant,
        on_delete=models.PROTECT,
        related_name="submitted_ideas",
        null=True,
        blank=True,
    )
    submitted_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_ideas",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    promoted_to_option = models.ForeignKey(
        "decision_options.DecisionOption",
        on_delete=models.PROTECT,
        related_name="promoted_from_idea",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(title=""), name="idea_title_not_empty"),
            models.CheckConstraint(
                condition=models.Q(status__in=["submitted", "shortlisted", "promoted", "archived"]),
                name="idea_status_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(submitted_by_participant__isnull=False, submitted_by_user__isnull=True)
                    | models.Q(submitted_by_participant__isnull=True, submitted_by_user__isnull=False)
                ),
                name="idea_submitter_exactly_one_identity",
            ),
        ]
        indexes = [
            models.Index(fields=["session", "status"], name="idea_session_status_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.category = self.category.strip()
        has_participant = self.submitted_by_participant_id is not None
        has_user = self.submitted_by_user_id is not None
        if has_participant == has_user:
            raise ValidationError("An idea must be submitted by exactly one identity.")
        if has_participant and self.submitted_by_participant.session_id != self.session_id:
            raise ValidationError(
                {"submitted_by_participant": "The submitter must belong to this session."}
            )
        if self.status == self.Status.PROMOTED and not self.promoted_to_option_id:
            raise ValidationError("A promoted idea requires its resulting option.")
        if self.status != self.Status.PROMOTED and self.promoted_to_option_id:
            raise ValidationError("Only a promoted idea may reference a resulting option.")

    def __str__(self) -> str:
        return f"{self.session.title}: {self.title}"


class IdeaComment(UUIDTimeStampedModel):
    """One deliberation message on an idea, from a participant or an org member."""

    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField()
    participant = models.ForeignKey(
        SessionParticipant,
        on_delete=models.PROTECT,
        related_name="idea_comments",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="idea_comments",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(condition=~models.Q(body=""), name="idea_comment_body_not_empty"),
            models.CheckConstraint(
                condition=(
                    models.Q(participant__isnull=False, user__isnull=True)
                    | models.Q(participant__isnull=True, user__isnull=False)
                ),
                name="idea_comment_exactly_one_identity",
            ),
        ]
        indexes = [
            models.Index(fields=["idea", "created_at"], name="idea_comment_idea_created_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()
        has_participant = self.participant_id is not None
        has_user = self.user_id is not None
        if has_participant == has_user:
            raise ValidationError("A comment must come from exactly one identity.")
        if has_participant and self.participant.session_id != self.idea.session_id:
            raise ValidationError({"participant": "The commenter must belong to this session."})

    def __str__(self) -> str:
        who = self.participant.name if self.participant_id else self.user.email  # type: ignore[union-attr]
        return f"{who} on {self.idea.title}"


class IdeaVote(UUIDTimeStampedModel):
    """One identity's support for one idea. Toggled, not ranked."""

    idea = models.ForeignKey(Idea, on_delete=models.CASCADE, related_name="votes")
    participant = models.ForeignKey(
        SessionParticipant,
        on_delete=models.PROTECT,
        related_name="votes",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="idea_votes",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(participant__isnull=False, user__isnull=True)
                    | models.Q(participant__isnull=True, user__isnull=False)
                ),
                name="idea_vote_exactly_one_identity",
            ),
            models.UniqueConstraint(
                fields=["idea", "participant"],
                condition=models.Q(participant__isnull=False),
                name="unique_vote_per_idea_participant",
            ),
            models.UniqueConstraint(
                fields=["idea", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_vote_per_idea_user",
            ),
        ]

    def clean(self) -> None:
        super().clean()
        has_participant = self.participant_id is not None
        has_user = self.user_id is not None
        if has_participant == has_user:
            raise ValidationError("A vote must come from exactly one identity.")
        if has_participant and self.participant.session_id != self.idea.session_id:
            raise ValidationError({"participant": "The voter must belong to this session."})

    def __str__(self) -> str:
        who = self.participant.name if self.participant_id else self.user.email  # type: ignore[union-attr]
        return f"{who} → {self.idea.title}"
