"""Root URL configuration."""

from django.contrib import admin
from django.urls import include, path

from apps.core.views import LivenessView, ReadinessView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/live/", LivenessView.as_view(), name="health-live"),
    path("health/ready/", ReadinessView.as_view(), name="health-ready"),
    path("api/v1/auth/", include("apps.accounts.urls")),
    path("api/v1/organisations/", include("apps.organisations.urls")),
    path("api/v1/", include("apps.invitations.urls")),
    path("api/v1/", include("apps.audit.urls")),
    path("api/v1/", include("apps.workspaces.urls")),
    path("api/v1/", include("apps.decisions.urls")),
    path("api/v1/", include("apps.participants.urls")),
    path("api/v1/", include("apps.positions.urls")),
    path("api/v1/", include("apps.decision_options.urls")),
    path("api/v1/", include("apps.evidence.urls")),
    path("api/v1/", include("apps.assumptions.urls")),
    path("api/v1/", include("apps.risks.urls")),
    path("api/v1/", include("apps.reviews.urls")),
    path("api/v1/", include("apps.lessons.urls")),
    path("api/v1/", include("apps.search.urls")),
]
