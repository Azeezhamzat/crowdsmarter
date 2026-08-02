from django.contrib import admin

from .models import Assumption


@admin.register(Assumption)
class AssumptionAdmin(admin.ModelAdmin):
    list_display = ("summary", "decision", "confidence", "verification_status", "status")
    list_filter = ("confidence", "verification_status", "status")
    search_fields = ("statement", "decision__title")
    readonly_fields = [field.name for field in Assumption._meta.fields]

    @admin.display(description="Assumption")
    def summary(self, obj):  # type: ignore[no-untyped-def]
        return obj.statement[:80]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
