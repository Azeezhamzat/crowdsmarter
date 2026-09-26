"""Organisation API routes."""

from django.urls import path

from .views import (
    MembershipDetailView,
    MembershipListView,
    OrganisationAdministrationView,
    OrganisationDeactivateView,
    OrganisationDeletionRequestCancelView,
    OrganisationDeletionRequestListCreateView,
    OrganisationDetailView,
    OrganisationListCreateView,
    OrganisationMembershipHistoryView,
    OrganisationOwnershipTransferView,
    OrganisationReactivateView,
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
    path(
        "<uuid:organisation_id>/administration/",
        OrganisationAdministrationView.as_view(),
        name="administration",
    ),
    path(
        "<uuid:organisation_id>/membership-history/",
        OrganisationMembershipHistoryView.as_view(),
        name="membership-history",
    ),
    path(
        "<uuid:organisation_id>/transfer-ownership/",
        OrganisationOwnershipTransferView.as_view(),
        name="transfer-ownership",
    ),
    path(
        "<uuid:organisation_id>/deactivate/",
        OrganisationDeactivateView.as_view(),
        name="deactivate",
    ),
    path(
        "<uuid:organisation_id>/reactivate/",
        OrganisationReactivateView.as_view(),
        name="reactivate",
    ),
    path(
        "<uuid:organisation_id>/deletion-requests/",
        OrganisationDeletionRequestListCreateView.as_view(),
        name="deletion-requests",
    ),
    path(
        "deletion-requests/<uuid:request_id>/cancel/",
        OrganisationDeletionRequestCancelView.as_view(),
        name="deletion-request-cancel",
    ),
]
