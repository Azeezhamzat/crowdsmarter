from django.contrib import admin

from .models import DiscussionEntry


@admin.register(DiscussionEntry)
class DiscussionEntryAdmin(admin.ModelAdmin):
    list_display = ("decision", "kind", "author", "is_resolved", "created_at")
    list_filter = ("kind", "resolved_at", "organisation")
    search_fields = ("decision__title", "author__email", "body")
    readonly_fields = (
        "organisation",
        "decision",
        "author",
        "kind",
        "body",
        "reply_to",
        "mentioned_users",
        "resolved_at",
        "resolved_by",
        "resolution_note",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
