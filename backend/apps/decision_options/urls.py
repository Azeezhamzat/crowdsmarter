from django.urls import path

from .views import (
    DecisionOptionDetailView,
    DecisionOptionEligibilityView,
    DecisionOptionListCreateView,
    DecisionOptionOutcomeView,
    OrganisationBudgetRollupView,
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
    path(
        "organisations/<uuid:organisation_id>/budget-rollup/",
        OrganisationBudgetRollupView.as_view(),
        name="budget-rollup",
    ),
]
