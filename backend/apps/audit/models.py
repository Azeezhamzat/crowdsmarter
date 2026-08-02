"""Append-only audit records for attributable system changes."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class AuditEventQuerySet(models.QuerySet["AuditEvent"]):
    """Prevent mutation through bulk queryset operations."""

    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Audit events are append-only and cannot be updated.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only and cannot be deleted.")


class AuditEvent(UUIDTimeStampedModel):
    """An immutable, attributable record of a material action."""

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=120)
    object_type = models.CharField(max_length=120)
    object_id = models.CharField(max_length=64)
    metadata = models.JSONField(default=dict, blank=True)

    objects = AuditEventQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["organisation", "-created_at"],
                name="audit_org_created_idx",
            ),
            models.Index(
                fields=["object_type", "object_id"],
                name="audit_object_idx",
            ),
            models.Index(
                fields=["action", "-created_at"],
                name="audit_action_created_idx",
            ),
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self._state.adding is False:
            raise ValidationError("Audit events are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Audit events are append-only and cannot be deleted.")

    def __str__(self) -> str:
        return f"{self.action}: {self.object_type}/{self.object_id}"
