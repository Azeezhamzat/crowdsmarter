"""Decision API routes."""

from django.urls import path

from .views import (
    DecisionDetailView,
    DecisionFinalisationView,
    DecisionListCreateView,
    DecisionOverviewView,
    DecisionTemplateListView,
    DecisionTransitionListCreateView,
)

app_name = "decisions"

urlpatterns = [
    path("decision-templates/", DecisionTemplateListView.as_view(), name="template-list"),
    path(
        "workspaces/<uuid:workspace_id>/decisions/",
        DecisionListCreateView.as_view(),
        name="list-create",
    ),
    path("decisions/<uuid:decision_id>/", DecisionDetailView.as_view(), name="detail"),
    path("decisions/<uuid:decision_id>/overview/", DecisionOverviewView.as_view(), name="overview"),
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
