"""Applicant portal API routes: all public, gated by the bearer flows themselves."""

from django.urls import path

from .views import (
    MagicLinkConsumeView,
    MagicLinkRequestView,
    MyApplicationsView,
    ProgressReportCreateView,
)

app_name = "applicants"

urlpatterns = [
    path("applicants/magic-link/", MagicLinkRequestView.as_view(), name="magic-link-request"),
    path("applicants/magic-link/consume/", MagicLinkConsumeView.as_view(), name="magic-link-consume"),
    path("applicants/me/applications/", MyApplicationsView.as_view(), name="my-applications"),
    path(
        "applicants/me/applications/<uuid:idea_id>/progress-reports/",
        ProgressReportCreateView.as_view(),
        name="progress-report-create",
    ),
]
