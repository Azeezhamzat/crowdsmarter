"""Organisation-owned containers for related decisions."""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.db import models

from apps.core.models import UUIDTimeStampedModel


class WorkspaceQuerySet(models.QuerySet["Workspace"]):
    """Tenant-safe workspace queries."""

    def for_user(self, user: Any) -> models.QuerySet["Workspace"]:
        if user.is_anonymous:
            return self.none()
        return self.filter(
            organisation__memberships__user=user,
            organisation__memberships__status="active",
        ).distinct()


class Workspace(UUIDTimeStampedModel):
    """A focused decision area within one organisation."""

    organisation = models.ForeignKey(
        "organisations.Organisation",
        on_delete=models.CASCADE,
        related_name="workspaces",
    )
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=80)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_workspaces",
    )

    objects = WorkspaceQuerySet.as_manager()

    class Meta:
        ordering = ["name", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["organisation", "slug"],
                name="unique_workspace_slug_per_org",
            ),
            models.UniqueConstraint(
                fields=["organisation"],
                condition=models.Q(is_default=True),
                name="one_default_workspace_per_org",
            ),
            models.CheckConstraint(
                condition=~models.Q(name=""),
                name="workspace_name_not_empty",
            ),
            models.CheckConstraint(
                condition=~models.Q(slug=""),
                name="workspace_slug_not_empty",
            ),
        ]
        indexes = [
            models.Index(
                fields=["organisation", "name"],
                name="workspace_org_name_idx",
            )
        ]

    def clean(self) -> None:
        """Normalise mutable workspace fields."""
        super().clean()
        self.name = self.name.strip()
        self.slug = self.slug.strip().lower()
        self.description = self.description.strip()

    def __str__(self) -> str:
        return f"{self.organisation.name}: {self.name}"
