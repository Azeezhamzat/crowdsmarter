from django.contrib import admin

from .models import Risk


@admin.register(Risk)
class RiskAdmin(admin.ModelAdmin):
    list_display = ("title", "decision", "likelihood", "impact", "score_value", "status")
    list_filter = ("response_strategy", "status")
    search_fields = ("title", "description", "decision__title")
    readonly_fields = [field.name for field in Risk._meta.fields]

    @admin.display(description="Score")
    def score_value(self, obj):  # type: ignore[no-untyped-def]
        return obj.score

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
