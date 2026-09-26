from django.urls import path

from .views import (
    DecisionMethodDetailView,
    DecisionMethodNewVersionView,
    DecisionMethodRetireView,
    DecisionMethodVersionApproveView,
    DecisionMethodVersionDetailView,
    OrganisationMethodCloneView,
    OrganisationMethodListCreateView,
    OrganisationMethodUsageView,
)

app_name = "methodology"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/decision-methods/",
        OrganisationMethodListCreateView.as_view(),
        name="method-list-create",
    ),
    path(
        "organisations/<uuid:organisation_id>/decision-methods/clone/",
        OrganisationMethodCloneView.as_view(),
        name="method-clone",
    ),
    path(
        "organisations/<uuid:organisation_id>/decision-method-usage/",
        OrganisationMethodUsageView.as_view(),
        name="method-usage",
    ),
    path(
        "decision-methods/<uuid:method_id>/",
        DecisionMethodDetailView.as_view(),
        name="method-detail",
    ),
    path(
        "decision-methods/<uuid:method_id>/versions/",
        DecisionMethodNewVersionView.as_view(),
        name="method-new-version",
    ),
    path(
        "decision-methods/<uuid:method_id>/retire/",
        DecisionMethodRetireView.as_view(),
        name="method-retire",
    ),
    path(
        "decision-method-versions/<uuid:version_id>/",
        DecisionMethodVersionDetailView.as_view(),
        name="version-detail",
    ),
    path(
        "decision-method-versions/<uuid:version_id>/approve/",
        DecisionMethodVersionApproveView.as_view(),
        name="version-approve",
    ),
]
