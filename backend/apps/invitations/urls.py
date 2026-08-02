"""Organisation invitation API routes."""

from django.urls import path

from .views import (
    InvitationAcceptView,
    InvitationListCreateView,
    InvitationResendView,
    InvitationRevokeView,
)

app_name = "invitations"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/invitations/",
        InvitationListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "organisation-invitations/<uuid:invitation_id>/resend/",
        InvitationResendView.as_view(),
        name="resend",
    ),
    path(
        "organisation-invitations/<uuid:invitation_id>/revoke/",
        InvitationRevokeView.as_view(),
        name="revoke",
    ),
    path(
        "invitations/accept/",
        InvitationAcceptView.as_view(),
        name="accept",
    ),
]
