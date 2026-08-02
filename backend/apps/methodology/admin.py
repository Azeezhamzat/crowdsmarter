"""Read-only operational inspection for governed organisation methods."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import DecisionMethod, DecisionMethodUsage, DecisionMethodVersion


@admin.register(DecisionMethod)
class DecisionMethodAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["name", "organisation", "status", "current_version", "created_at"]
    list_filter = ["status"]
    search_fields = ["name", "organisation__name", "key"]


@admin.register(DecisionMethodVersion)
class DecisionMethodVersionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["method", "version", "status", "approved_by", "approved_at"]
    list_filter = ["status", "suggested_urgency"]
    search_fields = ["method__name", "organisation__name"]


@admin.register(DecisionMethodUsage)
class DecisionMethodUsageAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ["method_version", "decision", "organisation", "applied_by", "created_at"]
    search_fields = ["method_version__method__name", "decision__title", "organisation__name"]
