from django.contrib import admin

from .models import PlatformAdministrator, PlatformConfiguration, SupportAccessGrant


@admin.register(PlatformAdministrator)
class PlatformAdministratorAdmin(admin.ModelAdmin):
    list_display = ("user", "status", "granted_by", "created_at", "suspended_at")
    list_filter = ("status",)
    search_fields = ("user__email", "rationale")
    readonly_fields = ("created_at", "updated_at")


@admin.register(PlatformConfiguration)
class PlatformConfigurationAdmin(admin.ModelAdmin):
    readonly_fields = ("singleton_key", "created_at", "updated_at")

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return not PlatformConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False


@admin.register(SupportAccessGrant)
class SupportAccessGrantAdmin(admin.ModelAdmin):
    list_display = (
        "administrator",
        "organisation",
        "access_level",
        "status",
        "expires_at",
        "created_at",
    )
    list_filter = ("status", "access_level")
    search_fields = ("administrator__email", "organisation__name", "reason")
    readonly_fields = ("created_at", "updated_at")
