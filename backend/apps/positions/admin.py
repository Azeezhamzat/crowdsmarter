from django.contrib import admin

from .models import Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = (
        "decision",
        "participant",
        "recommendation",
        "preferred_option",
        "version",
        "created_at",
    )
    list_filter = ("recommendation", "confidence", "created_at")
    search_fields = ("decision__title", "participant__user__email", "rationale")
    readonly_fields = [field.name for field in Position._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
