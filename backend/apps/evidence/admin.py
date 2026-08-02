from django.contrib import admin

from .models import Evidence


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "decision", "source_type", "stance", "strength", "status")
    list_filter = ("source_type", "stance", "strength", "status")
    search_fields = ("title", "summary", "decision__title")
    readonly_fields = [field.name for field in Evidence._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
