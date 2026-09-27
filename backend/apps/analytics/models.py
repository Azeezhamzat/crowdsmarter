"""Attributable, replayable AI analytics insights."""

from __future__ import annotations

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class AnalyticsInsight(UUIDTimeStampedModel):
    """One provider-generated narrative over an organisation's decision metrics."""

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.PROTECT,
        related_name="analytics_insights",
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requested_analytics_insights",
    )
    provider_key = models.CharField(max_length=120)
    provider_label = models.CharField(max_length=240)
    model_identifier = models.CharField(max_length=240, blank=True)
    metrics_snapshot = models.JSONField(default=dict, encoder=DjangoJSONEncoder)
    headline = models.TextField()
    observations = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(provider_key=""),
                name="analytics_insight_provider_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(headline=""),
                name="analytics_insight_headline_not_empty",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "-created_at"],
                name="analytics_insight_org_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.organisation.name}: {self.provider_label} insight ({self.created_at:%Y-%m-%d})"
        )
