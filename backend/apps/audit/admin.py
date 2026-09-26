"""Read-only audit administration."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Expose audit events as read-only operational evidence."""

    list_display = ["created_at", "action", "object_type", "object_id", "actor", "organisation"]
    list_filter = ["action", "object_type"]
    search_fields = ["object_id", "actor__email", "organisation__name"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "action",
        "object_type",
        "object_id",
        "actor",
        "organisation",
        "metadata",
    ]
