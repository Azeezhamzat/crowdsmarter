"""Read-only operational views for tenant governance.

Tenant and membership writes must pass through audited service workflows; the
Django admin intentionally cannot bypass those invariants.
"""

from django.contrib import admin

from apps.core.admin import ReadOnlyAdminMixin

from .models import Membership, Organisation


class MembershipInline(admin.TabularInline):
    """Show organisation members without allowing invariant bypass."""

    model = Membership
    extra = 0
    can_delete = False
    fields = ["id", "user", "role", "status", "created_at", "updated_at"]
    readonly_fields = fields

    def has_add_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False


@admin.register(Organisation)
class OrganisationAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect organisations; use the product workflow for writes."""

    list_display = ["name", "slug", "created_by", "created_at"]
    search_fields = ["name", "slug", "created_by__email"]
    readonly_fields = ["id", "name", "slug", "created_by", "created_at", "updated_at"]
    inlines = [MembershipInline]


@admin.register(Membership)
class MembershipAdmin(ReadOnlyAdminMixin, admin.ModelAdmin):
    """Inspect memberships; use audited services for writes."""

    list_display = ["user", "organisation", "role", "status", "created_at"]
    list_filter = ["role", "status"]
    search_fields = ["user__email", "organisation__name"]
    readonly_fields = [
        "id",
        "user",
        "organisation",
        "role",
        "status",
        "created_at",
        "updated_at",
    ]
