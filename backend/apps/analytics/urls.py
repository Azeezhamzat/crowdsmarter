"""Analytics API routes."""

from django.urls import path

from .views import (
    OrganisationAnalyticsInsightHistoryView,
    OrganisationAnalyticsInsightView,
    OrganisationAnalyticsView,
)

app_name = "analytics"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/analytics/",
        OrganisationAnalyticsView.as_view(),
        name="organisation",
    ),
    path(
        "organisations/<uuid:organisation_id>/analytics/insight/",
        OrganisationAnalyticsInsightView.as_view(),
        name="organisation-insight",
    ),
    path(
        "organisations/<uuid:organisation_id>/analytics/insight/history/",
        OrganisationAnalyticsInsightHistoryView.as_view(),
        name="organisation-insight-history",
    ),
]
