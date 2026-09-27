"""Admin registration for accounts."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import EmailChangeRequest, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Manage email-based users safely in Django admin."""

    ordering = ["email"]
    list_display = ["email", "first_name", "last_name", "is_staff", "is_active"]
    search_fields = ["email", "first_name", "last_name"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal information", {"fields": ("first_name", "last_name")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        """Require explicit account lifecycle workflows rather than hard deletion."""
        return False

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "is_staff", "is_active"),
            },
        ),
    )


@admin.register(EmailChangeRequest)
class EmailChangeRequestAdmin(admin.ModelAdmin):
    """Read-only visibility into account email-verification activity."""

    list_display = [
        "user",
        "new_email",
        "created_at",
        "expires_at",
        "completed_at",
        "invalidated_at",
    ]
    search_fields = ["user__email", "new_email"]
    readonly_fields = [
        "id",
        "user",
        "new_email",
        "token_digest",
        "created_at",
        "updated_at",
        "expires_at",
        "completed_at",
        "invalidated_at",
    ]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
