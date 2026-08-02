"""Read-only participant administration."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import Participant


@admin.register(Participant)
class ParticipantAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect participation history; use audited services for writes."""

    list_display = ("user", "decision", "role", "status", "created_at")
    list_filter = ("role", "status")
    search_fields = ("user__email", "decision__title", "organisation__name")
    readonly_fields = [field.name for field in Participant._meta.fields]
