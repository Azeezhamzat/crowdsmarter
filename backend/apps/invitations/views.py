"""Thin REST endpoints for invitation workflows."""

from __future__ import annotations

from django.contrib.auth import login
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.serializers import UserSerializer
from apps.organisations.permissions import IsOrganisationMember
from apps.organisations.selectors import organisation_for_user
from apps.organisations.serializers import MembershipSerializer

from .models import OrganisationInvitation
from .permissions import CanManageInvitations
from .selectors import invitation_by_token, invitation_for_manager, invitations_for_manager
from .serializers import (
    InvitationAcceptSerializer,
    InvitationCreateSerializer,
    InvitationPublicSerializer,
    InvitationSerializer,
)
from .services import (
    accept_invitation,
    create_invitation,
    deliver_invitation,
    revoke_invitation,
    rotate_invitation,
)
from .throttles import InvitationAcceptanceThrottle, InvitationManagementThrottle


def _dispatch_payload(invitation, delivery):  # type: ignore[no-untyped-def]
    return {
        "invitation": InvitationSerializer(invitation).data,
        "delivery": {
            "status": delivery.status,
            "acceptance_url": delivery.acceptance_url,
        },
    }


def _no_store(response: Response) -> Response:
    response["Cache-Control"] = "no-store"
    response["Referrer-Policy"] = "no-referrer"
    return response


class InvitationListCreateView(APIView):
    """List or create invitations for one organisation."""

    permission_classes = [IsAuthenticated, IsOrganisationMember, CanManageInvitations]
    throttle_classes = [InvitationManagementThrottle]

    def _get_organisation(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(
            user=request.user,
            organisation_id=organisation_id,
        )
        self.check_object_permissions(request, organisation)
        return organisation

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        self._get_organisation(request, organisation_id)
        invitations = invitations_for_manager(
            user=request.user,
            organisation_id=str(organisation_id),
        )
        return Response(InvitationSerializer(invitations, many=True).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = self._get_organisation(request, organisation_id)
        serializer = InvitationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, raw_token = create_invitation(
            actor=request.user,
            organisation=organisation,
            **serializer.validated_data,
        )
        delivery = deliver_invitation(
            invitation=invitation,
            raw_token=raw_token,
            actor=request.user,
        )
        return _no_store(
            Response(
                _dispatch_payload(invitation, delivery),
                status=status.HTTP_201_CREATED,
            )
        )


class InvitationResendView(APIView):
    """Rotate and resend one manager-visible invitation."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [InvitationManagementThrottle]

    def post(self, request, invitation_id):  # type: ignore[no-untyped-def]
        try:
            invitation = invitation_for_manager(
                user=request.user,
                invitation_id=str(invitation_id),
            )
        except OrganisationInvitation.DoesNotExist as exc:
            raise Http404 from exc
        invitation, raw_token = rotate_invitation(
            actor=request.user,
            invitation=invitation,
        )
        delivery = deliver_invitation(
            invitation=invitation,
            raw_token=raw_token,
            actor=request.user,
        )
        return _no_store(Response(_dispatch_payload(invitation, delivery)))


class InvitationRevokeView(APIView):
    """Revoke one manager-visible invitation."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [InvitationManagementThrottle]

    def post(self, request, invitation_id):  # type: ignore[no-untyped-def]
        try:
            invitation = invitation_for_manager(
                user=request.user,
                invitation_id=str(invitation_id),
            )
        except OrganisationInvitation.DoesNotExist as exc:
            raise Http404 from exc
        invitation = revoke_invitation(actor=request.user, invitation=invitation)
        return Response(InvitationSerializer(invitation).data)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class InvitationAcceptView(APIView):
    """Inspect or accept an invitation using its one-time secret."""

    permission_classes = [AllowAny]
    throttle_classes = [InvitationAcceptanceThrottle]

    def _raw_token(self, request) -> str:  # type: ignore[no-untyped-def]
        raw_token = request.headers.get("X-Invitation-Token", "").strip()
        if not raw_token:
            raise Http404
        return raw_token

    def _get_invitation(self, raw_token: str) -> OrganisationInvitation:
        try:
            return invitation_by_token(raw_token=raw_token)
        except OrganisationInvitation.DoesNotExist as exc:
            raise Http404 from exc

    def get(self, request):  # type: ignore[no-untyped-def]
        raw_token = self._raw_token(request)
        invitation = self._get_invitation(raw_token)
        data = dict(InvitationPublicSerializer(invitation).data)
        data["current_user_email"] = (
            request.user.email if request.user.is_authenticated else None
        )
        return _no_store(Response(data))

    def post(self, request):  # type: ignore[no-untyped-def]
        raw_token = self._raw_token(request)
        self._get_invitation(raw_token)
        serializer = InvitationAcceptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        authenticated_user = request.user if request.user.is_authenticated else None
        user, membership, created_user = accept_invitation(
            raw_token=raw_token,
            authenticated_user=authenticated_user,
            **serializer.validated_data,
        )
        if created_user:
            login(request, user)
        return _no_store(
            Response(
                {
                    "user": UserSerializer(user).data,
                    "membership": MembershipSerializer(membership).data,
                    "created_account": created_user,
                },
                status=status.HTTP_201_CREATED,
            )
        )
