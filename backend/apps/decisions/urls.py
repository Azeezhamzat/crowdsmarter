"""Decision API routes."""

from django.urls import path

from .views import (
    DecisionDetailView,
    DecisionFinalisationView,
    DecisionListCreateView,
    DecisionTransitionListCreateView,
)

app_name = "decisions"

urlpatterns = [
    path(
        "workspaces/<uuid:workspace_id>/decisions/",
        DecisionListCreateView.as_view(),
        name="list-create",
    ),
    path("decisions/<uuid:decision_id>/", DecisionDetailView.as_view(), name="detail"),
    path(
        "decisions/<uuid:decision_id>/finalisation/",
        DecisionFinalisationView.as_view(),
        name="finalisation",
    ),
    path(
        "decisions/<uuid:decision_id>/transitions/",
        DecisionTransitionListCreateView.as_view(),
        name="transition-list-create",
    ),
]
