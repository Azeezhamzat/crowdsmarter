from django.contrib import admin

from .models import Criterion


@admin.register(Criterion)
class CriterionAdmin(admin.ModelAdmin):
    list_display = ("title", "decision", "weight", "direction", "is_must_have", "status")
    list_filter = ("direction", "is_must_have", "status")
    search_fields = ("title", "description", "decision__title")
    readonly_fields = [field.name for field in Criterion._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
