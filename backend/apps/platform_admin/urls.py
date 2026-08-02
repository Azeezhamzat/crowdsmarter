from django.urls import path

app_name = "platform_admin"

from .views import (
    PlatformAdministratorActionView,
    PlatformAdministratorListView,
    PlatformAuditListView,
    PlatformConfigurationView,
    PlatformDemoRequestListView,
    PlatformDemoRequestStatusView,
    PlatformInvitationActionView,
    PlatformOrganisationDetailView,
    PlatformOrganisationListView,
    PlatformOrganisationOwnershipView,
    PlatformOrganisationStateView,
    PlatformOverviewView,
    PlatformSupportAccessCreateView,
    PlatformSupportAccessRevokeView,
    PlatformUserListView,
    PlatformUserStateView,
    PublicPlatformConfigurationView,
)

urlpatterns = [
    path("public/configuration/", PublicPlatformConfigurationView.as_view(), name="public-platform-configuration"),
    path("platform-admin/overview/", PlatformOverviewView.as_view(), name="platform-admin-overview"),
    path("platform-admin/organisations/", PlatformOrganisationListView.as_view(), name="platform-admin-organisations"),
    path("platform-admin/organisations/<uuid:organisation_id>/", PlatformOrganisationDetailView.as_view(), name="platform-admin-organisation-detail"),
    path("platform-admin/organisations/<uuid:organisation_id>/support-access/", PlatformSupportAccessCreateView.as_view(), name="platform-admin-support-access-create"),
    path("platform-admin/support-access/<uuid:grant_id>/revoke/", PlatformSupportAccessRevokeView.as_view(), name="platform-admin-support-access-revoke"),
    path("platform-admin/organisations/<uuid:organisation_id>/ownership/", PlatformOrganisationOwnershipView.as_view(), name="platform-admin-organisation-ownership"),
    path("platform-admin/organisations/<uuid:organisation_id>/state/", PlatformOrganisationStateView.as_view(), name="platform-admin-organisation-state"),
    path("platform-admin/invitations/<uuid:invitation_id>/action/", PlatformInvitationActionView.as_view(), name="platform-admin-invitation-action"),
    path("platform-admin/users/", PlatformUserListView.as_view(), name="platform-admin-users"),
    path("platform-admin/users/<uuid:user_id>/state/", PlatformUserStateView.as_view(), name="platform-admin-user-state"),
    path("platform-admin/administrators/", PlatformAdministratorListView.as_view(), name="platform-admin-administrators"),
    path("platform-admin/users/<uuid:user_id>/administrator/", PlatformAdministratorActionView.as_view(), name="platform-admin-administrator-action"),
    path("platform-admin/configuration/", PlatformConfigurationView.as_view(), name="platform-admin-configuration"),
    path("platform-admin/demo-requests/", PlatformDemoRequestListView.as_view(), name="platform-admin-demo-requests"),
    path("platform-admin/demo-requests/<uuid:demo_request_id>/status/", PlatformDemoRequestStatusView.as_view(), name="platform-admin-demo-request-status"),
    path("platform-admin/audit/", PlatformAuditListView.as_view(), name="platform-admin-audit"),
]
