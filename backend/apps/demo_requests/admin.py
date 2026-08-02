"""Administrative review of public demo requests."""

from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    """Expose a restrained lead-review surface to Django administrators."""

    list_display = (
        "full_name",
        "organisation_name",
        "work_email",
        "primary_need",
        "status",
        "created_at",
    )
    list_filter = ("status", "primary_need", "organisation_size", "created_at")
    search_fields = ("full_name", "work_email", "organisation_name", "job_title")
    readonly_fields = (
        "id",
        "full_name",
        "work_email",
        "organisation_name",
        "job_title",
        "organisation_size",
        "primary_need",
        "message",
        "consent_to_contact",
        "created_at",
        "updated_at",
    )
    fields = readonly_fields + ("status",)
