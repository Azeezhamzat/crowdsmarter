"""Append-only decision discussion records with explicit resolution."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class DiscussionEntryQuerySet(models.QuerySet["DiscussionEntry"]):
    """Prevent bulk mutation or deletion of discussion history."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Discussion entries cannot be bulk updated.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Discussion entries are append-only and cannot be deleted.")


class DiscussionEntry(UUIDTimeStampedModel):
    """An attributable note, question, concern, or update on one decision."""

    class Kind(models.TextChoices):
        NOTE = "note", "Note"
        QUESTION = "question", "Question"
        CONCERN = "concern", "Concern"
        UPDATE = "update", "Update"

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="discussion_entries",
    )
    decision = models.ForeignKey(
        "decisions.Decision",
        on_delete=models.CASCADE,
        related_name="discussion_entries",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="discussion_entries",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices)
    body = models.TextField()
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        related_name="replies",
        null=True,
        blank=True,
    )
    mentioned_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="discussion_mentions",
        blank=True,
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="resolved_discussion_entries",
        null=True,
        blank=True,
    )
    resolution_note = models.TextField(blank=True)

    objects = DiscussionEntryQuerySet.as_manager()

    class Meta:
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(kind__in=["note", "question", "concern", "update"]),
                name="discussion_entry_kind_valid",
            ),
            models.CheckConstraint(
                condition=~models.Q(body=""),
                name="discussion_entry_body_not_empty",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        resolved_at__isnull=True,
                        resolved_by__isnull=True,
                        resolution_note="",
                    )
                    | models.Q(
                        resolved_at__isnull=False,
                        resolved_by__isnull=False,
                    )
                ),
                name="discussion_resolution_fields_consistent",
            ),
        ]
        indexes = [
            models.Index(
                fields=["decision", "-created_at"],
                name="discussion_decision_time_idx",
            ),
            models.Index(
                fields=["organisation", "kind", "-created_at"],
                name="discussion_org_kind_idx",
            ),
        ]

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()
        self.resolution_note = self.resolution_note.strip()
        if self.decision_id and self.organisation_id:
            if self.decision.organisation_id != self.organisation_id:
                raise ValidationError(
                    {"organisation": "The entry must share the decision organisation."}
                )
        if self.reply_to_id and self.reply_to.decision_id != self.decision_id:
            raise ValidationError(
                {"reply_to": "A reply must belong to the same decision."}
            )
        if self.resolved_at and self.kind not in {
            self.Kind.QUESTION,
            self.Kind.CONCERN,
        }:
            raise ValidationError(
                {"resolved_at": "Only questions and concerns can be resolved."}
            )
        if self.resolved_at and not self.resolution_note:
            raise ValidationError(
                {"resolution_note": "Record how the question or concern was resolved."}
            )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            original = DiscussionEntry.objects.get(pk=self.pk)
            immutable_fields = (
                "organisation_id",
                "decision_id",
                "author_id",
                "kind",
                "body",
                "reply_to_id",
                "created_at",
            )
            if any(getattr(original, field) != getattr(self, field) for field in immutable_fields):
                raise ValidationError("Discussion content is immutable; add a new entry instead.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Discussion entries are append-only and cannot be deleted.")

    def __str__(self) -> str:
        return f"{self.get_kind_display()} on {self.decision}"
