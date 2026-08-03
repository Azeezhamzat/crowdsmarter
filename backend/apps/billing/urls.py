from django.urls import path

from .views import (
    ChangePlanView,
    OrganisationSubscriptionView,
    PlanListView,
    SetBillingContactView,
)

app_name = "billing"

urlpatterns = [
    path("plans/", PlanListView.as_view(), name="plans"),
    path(
        "organisations/<uuid:organisation_id>/subscription/",
        OrganisationSubscriptionView.as_view(),
        name="subscription",
    ),
    path(
        "organisations/<uuid:organisation_id>/subscription/plan/",
        ChangePlanView.as_view(),
        name="change-plan",
    ),
    path(
        "organisations/<uuid:organisation_id>/subscription/billing-contact/",
        SetBillingContactView.as_view(),
        name="set-billing-contact",
    ),
]
