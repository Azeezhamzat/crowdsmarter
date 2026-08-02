"""Read-only decision administration."""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import Decision, DecisionFinalisation, DecisionTransition


@admin.register(Decision)
class DecisionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect decisions; use audited workflow services for writes."""

    list_display = ("title", "organisation", "workspace", "status", "owner", "updated_at")
    list_filter = ("status", "urgency")
    search_fields = ("title", "decision_question", "organisation__name")
    readonly_fields = [field.name for field in Decision._meta.fields]


@admin.register(DecisionTransition)
class DecisionTransitionAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect immutable lifecycle history."""

    list_display = ("decision", "sequence", "from_status", "to_status", "actor", "created_at")
    list_filter = ("from_status", "to_status")
    search_fields = ("decision__title", "actor__email")
    readonly_fields = [field.name for field in DecisionTransition._meta.fields]


@admin.register(DecisionFinalisation)
class DecisionFinalisationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect immutable human final decision records."""

    list_display = (
        "decision",
        "selected_option",
        "decided_by",
        "decided_at",
    )
    search_fields = ("decision__title", "selected_option__title", "decided_by__email")
    readonly_fields = [field.name for field in DecisionFinalisation._meta.fields]
