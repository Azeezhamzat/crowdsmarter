from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "kind", "title", "read_at", "created_at")
    list_filter = ("kind", "read_at")
    search_fields = ("recipient__email", "title", "message")
    readonly_fields = [field.name for field in Notification._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
