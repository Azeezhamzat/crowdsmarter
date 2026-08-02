"""Customer export routes."""

from django.urls import path

from .views import DecisionExportView, OrganisationExportView

app_name = "exports"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/exports/complete/",
        OrganisationExportView.as_view(),
        name="organisation-complete",
    ),
    path(
        "decisions/<uuid:decision_id>/export/",
        DecisionExportView.as_view(),
        name="decision-dossier",
    ),
]
