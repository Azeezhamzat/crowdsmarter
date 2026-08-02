from django.contrib import admin

from .models import DecisionReview


@admin.register(DecisionReview)
class DecisionReviewAdmin(admin.ModelAdmin):
    list_display = (
        "decision",
        "implementation_owner",
        "review_due_date",
        "outcome_assessment",
        "updated_at",
    )
    list_filter = ("outcome_assessment", "review_due_date")
    search_fields = ("decision__title", "implementation_owner__email")
    readonly_fields = [field.name for field in DecisionReview._meta.fields]

    def has_add_permission(self, request):  # type: ignore[no-untyped-def]
        return False

    def has_change_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False

    def has_delete_permission(self, request, obj=None):  # type: ignore[no-untyped-def]
        return False
