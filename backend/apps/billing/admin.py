from django.contrib import admin

from .models import OrganisationSubscription, Plan


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    """Packaging tiers are internal configuration, editable by platform staff."""

    list_display = ("name", "key", "order", "is_active", "max_active_decisions", "max_active_members")
    list_filter = ("is_active", "support_level")
    search_fields = ("key", "name")
    ordering = ("order",)


@admin.register(OrganisationSubscription)
class OrganisationSubscriptionAdmin(admin.ModelAdmin):
    """Subscription records are only created/changed through the service layer."""

    list_display = ("organisation", "plan", "status", "trial_ends_at", "billing_contact")
    list_filter = ("status", "plan")
    search_fields = ("organisation__name",)
    readonly_fields = [field.name for field in OrganisationSubscription._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
