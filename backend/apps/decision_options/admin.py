from django.contrib import admin

from .models import DecisionOption


@admin.register(DecisionOption)
class DecisionOptionAdmin(admin.ModelAdmin):
    list_display = ("title", "decision", "status", "is_status_quo", "created_at")
    list_filter = ("status", "is_status_quo")
    search_fields = ("title", "decision__title", "organisation__name")
    readonly_fields = [field.name for field in DecisionOption._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
