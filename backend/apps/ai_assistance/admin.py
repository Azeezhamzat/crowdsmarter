from django.contrib import admin

from .models import AIReview


@admin.register(AIReview)
class AIReviewAdmin(admin.ModelAdmin):
    list_display = (
        "decision",
        "provider_label",
        "status",
        "requested_by",
        "completed_at",
        "reviewed_at",
        "dismissed_at",
    )
    list_filter = ("status", "provider_key", "reviewed_at", "dismissed_at")
    search_fields = ("decision__title", "requested_by__email", "input_fingerprint")
    readonly_fields = [field.name for field in AIReview._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
