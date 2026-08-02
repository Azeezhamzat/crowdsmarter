"""Organisation API routes."""

from django.urls import path

from .views import (
    MembershipDetailView,
    MembershipListView,
    OrganisationDetailView,
    OrganisationListCreateView,
)

app_name = "organisations"

urlpatterns = [
    path("", OrganisationListCreateView.as_view(), name="list-create"),
    path("<uuid:organisation_id>/", OrganisationDetailView.as_view(), name="detail"),
    path(
        "<uuid:organisation_id>/memberships/",
        MembershipListView.as_view(),
        name="membership-list",
    ),
    path(
        "memberships/<uuid:membership_id>/",
        MembershipDetailView.as_view(),
        name="membership-detail",
    ),
]
