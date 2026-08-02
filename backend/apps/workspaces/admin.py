"""Read-only workspace administration."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect workspaces; use audited services for writes."""

    list_display = ("name", "organisation", "is_default", "created_at")
    list_filter = ("is_default",)
    search_fields = ("name", "slug", "organisation__name")
    readonly_fields = [field.name for field in Workspace._meta.fields]
