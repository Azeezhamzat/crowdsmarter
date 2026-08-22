from django.urls import path

from .views import (
    DecisionOptionDetailView,
    DecisionOptionEligibilityView,
    DecisionOptionListCreateView,
    DecisionOptionOutcomeView,
)

app_name = "decision_options"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/options/",
        DecisionOptionListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "decision-options/<uuid:option_id>/",
        DecisionOptionDetailView.as_view(),
        name="detail",
    ),
    path(
        "decision-options/<uuid:option_id>/eligibility/",
        DecisionOptionEligibilityView.as_view(),
        name="eligibility",
    ),
    path(
        "decision-options/<uuid:option_id>/outcome/",
        DecisionOptionOutcomeView.as_view(),
        name="outcome",
    ),
]
