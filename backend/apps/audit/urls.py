from django.urls import path

from .views import OrganisationAuditEventListView

app_name = "audit"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/audit-events/",
        OrganisationAuditEventListView.as_view(),
        name="organisation-events",
    ),
]
