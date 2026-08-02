"""Read-only operational inspection for invitation records."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import OrganisationInvitation


@admin.register(OrganisationInvitation)
class OrganisationInvitationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect invitations without exposing their original secret tokens."""

    list_display = [
        "email",
        "organisation",
        "role",
        "status",
        "expires_at",
        "last_sent_at",
    ]
    list_filter = ["status", "role"]
    search_fields = ["email", "organisation__name", "invited_by__email"]
    readonly_fields = [field.name for field in OrganisationInvitation._meta.fields]
