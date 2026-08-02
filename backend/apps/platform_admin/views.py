"""REST endpoints for platform administration and governed tenant support."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audit.models import AuditEvent
from apps.audit.serializers import AuditEventSerializer
from apps.demo_requests.models import DemoRequest
from apps.invitations.models import OrganisationInvitation
from apps.organisations.models import Membership, Organisation

from .models import PlatformAdministrator, PlatformConfiguration, SupportAccessGrant
from .permissions import IsPlatformAdministrator
from .selectors import (
    platform_audit_events,
    platform_demo_requests,
    platform_organisation_detail,
    platform_organisations,
    platform_users,
)
from .serializers import (
    PlatformAdministratorGrantSerializer,
    PlatformAdministratorSerializer,
    PlatformConfigurationSerializer,
    PlatformConfigurationUpdateSerializer,
    PlatformDemoRequestSerializer,
    PlatformDemoRequestStatusSerializer,
    PlatformInvitationActionSerializer,
    PlatformOrganisationDetailSerializer,
    PlatformOrganisationStateSerializer,
    PlatformOrganisationSummarySerializer,
    PlatformOwnershipTransferSerializer,
    PlatformUserSerializer,
    PlatformUserStateSerializer,
    SupportAccessCreateSerializer,
    SupportAccessGrantSerializer,
)
from .services import (
    create_support_access,
    current_support_access,
    grant_platform_administrator,
    platform_change_organisation_state,
    platform_invitation_action,
    platform_transfer_ownership,
    require_support_access,
    revoke_support_access,
    set_user_active,
    suspend_platform_administrator,
    update_demo_request_status,
    update_platform_configuration,
)

User = get_user_model()


class PlatformAdminBaseView(APIView):
    permission_classes = [IsAuthenticated, IsPlatformAdministrator]


class PublicPlatformConfigurationView(APIView):
    """Expose only public contact channels; never administrative policy or identities."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        item = PlatformConfiguration.load()
        response = Response(
            {
                "public_contact_email": item.public_contact_email,
                "demo_email": item.demo_email,
                "support_email": item.support_email,
                "privacy_email": item.privacy_email,
                "security_email": item.security_email,
            }
        )
        response["Cache-Control"] = "public, max-age=300"
        return response


class PlatformOverviewView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        now = timezone.now()
        SupportAccessGrant.objects.filter(
            status=SupportAccessGrant.Status.ACTIVE,
            expires_at__lte=now,
        ).update(status=SupportAccessGrant.Status.EXPIRED, updated_at=now)
        counts = {
            "users": User.objects.count(),
            "active_users": User.objects.filter(is_active=True).count(),
            "platform_administrators": PlatformAdministrator.objects.filter(
                status=PlatformAdministrator.Status.ACTIVE,
                user__is_active=True,
            ).count(),
            "organisations": Organisation.objects.count(),
            "active_organisations": Organisation.objects.filter(status=Organisation.Status.ACTIVE).count(),
            "deactivated_organisations": Organisation.objects.filter(
                status=Organisation.Status.DEACTIVATED
            ).count(),
            "active_decisions": sum(
                Organisation.objects.annotate(
                    active_count=Count("decisions", filter=~Q(decisions__status="archived"))
                ).values_list("active_count", flat=True)
            ),
            "pending_invitations": OrganisationInvitation.objects.filter(status="pending").count(),
            "new_demo_requests": DemoRequest.objects.filter(status=DemoRequest.Status.NEW).count(),
            "active_support_access": SupportAccessGrant.objects.filter(
                status=SupportAccessGrant.Status.ACTIVE,
                expires_at__gt=now,
            ).count(),
        }
        recent_events = platform_audit_events()[:12]
        recent_demo_requests = DemoRequest.objects.all().order_by("-created_at")[:8]
        active_grants = (
            SupportAccessGrant.objects.filter(
                status=SupportAccessGrant.Status.ACTIVE,
                expires_at__gt=now,
            )
            .select_related("administrator", "organisation", "revoked_by")
            .order_by("expires_at")[:12]
        )
        return Response(
            {
                "counts": counts,
                "recent_audit_events": AuditEventSerializer(recent_events, many=True).data,
                "recent_demo_requests": PlatformDemoRequestSerializer(recent_demo_requests, many=True).data,
                "active_support_access": SupportAccessGrantSerializer(active_grants, many=True).data,
            }
        )


class PlatformOrganisationListView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        queryset = platform_organisations(
            query=request.query_params.get("q", ""),
            status=request.query_params.get("status", ""),
        )
        return Response(PlatformOrganisationSummarySerializer(queryset, many=True).data)


class PlatformOrganisationDetailView(PlatformAdminBaseView):
    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = get_object_or_404(Organisation, id=organisation_id)
        require_support_access(actor=request.user, organisation=organisation)
        item = platform_organisation_detail(
            organisation_id=organisation_id,
            administrator=request.user,
        )
        return Response(
            PlatformOrganisationDetailSerializer(item, context={"request": request}).data
        )


class PlatformSupportAccessCreateView(PlatformAdminBaseView):
    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = get_object_or_404(Organisation, id=organisation_id)
        serializer = SupportAccessCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grant = create_support_access(
            actor=request.user,
            organisation=organisation,
            **serializer.validated_data,
        )
        return Response(SupportAccessGrantSerializer(grant).data, status=status.HTTP_201_CREATED)


class PlatformSupportAccessRevokeView(PlatformAdminBaseView):
    def post(self, request, grant_id):  # type: ignore[no-untyped-def]
        grant = get_object_or_404(SupportAccessGrant, id=grant_id)
        rationale = str(request.data.get("rationale", "")).strip()
        grant = revoke_support_access(actor=request.user, grant=grant, rationale=rationale)
        return Response(SupportAccessGrantSerializer(grant).data)


class PlatformOrganisationOwnershipView(PlatformAdminBaseView):
    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = get_object_or_404(Organisation, id=organisation_id)
        serializer = PlatformOwnershipTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = get_object_or_404(
            Membership,
            id=serializer.validated_data["target_membership_id"],
            organisation=organisation,
            status=Membership.Status.ACTIVE,
        )
        target = platform_transfer_ownership(
            actor=request.user,
            organisation=organisation,
            target_membership=target,
            rationale=serializer.validated_data["rationale"],
            confirmation=serializer.validated_data["confirmation"],
            demote_existing_owners=serializer.validated_data["demote_existing_owners"],
        )
        return Response(
            {
                "detail": f"Ownership transferred to {target.user.email}.",
                "target_membership_id": str(target.id),
            }
        )


class PlatformOrganisationStateView(PlatformAdminBaseView):
    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = get_object_or_404(Organisation, id=organisation_id)
        serializer = PlatformOrganisationStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = platform_change_organisation_state(
            actor=request.user,
            organisation=organisation,
            **serializer.validated_data,
        )
        return Response(PlatformOrganisationSummarySerializer(
            platform_organisations().get(id=organisation.id)
        ).data)


class PlatformInvitationActionView(PlatformAdminBaseView):
    def post(self, request, invitation_id):  # type: ignore[no-untyped-def]
        invitation = get_object_or_404(
            OrganisationInvitation.objects.select_related("organisation"),
            id=invitation_id,
        )
        serializer = PlatformInvitationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation, delivery = platform_invitation_action(
            actor=request.user,
            invitation=invitation,
            **serializer.validated_data,
        )
        return Response(
            {
                "detail": f"Invitation {serializer.validated_data['action']} completed.",
                "invitation_id": str(invitation.id),
                "status": invitation.status,
                **delivery,
            }
        )


class PlatformUserListView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        queryset = platform_users(
            query=request.query_params.get("q", ""),
            state=request.query_params.get("state", ""),
        )
        return Response(PlatformUserSerializer(queryset, many=True).data)


class PlatformUserStateView(PlatformAdminBaseView):
    def post(self, request, user_id):  # type: ignore[no-untyped-def]
        target = get_object_or_404(User, id=user_id)
        serializer = PlatformUserStateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = set_user_active(actor=request.user, user=target, **serializer.validated_data)
        annotated = platform_users().get(id=target.id)
        return Response(PlatformUserSerializer(annotated).data)


class PlatformAdministratorListView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        queryset = PlatformAdministrator.objects.select_related(
            "user", "granted_by", "suspended_by"
        ).all()
        return Response(PlatformAdministratorSerializer(queryset, many=True).data)


class PlatformAdministratorActionView(PlatformAdminBaseView):
    def post(self, request, user_id):  # type: ignore[no-untyped-def]
        target = get_object_or_404(User, id=user_id)
        serializer = PlatformAdministratorGrantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        if action == "grant":
            item = grant_platform_administrator(
                actor=request.user,
                user=target,
                rationale=serializer.validated_data["rationale"],
            )
        elif action == "suspend":
            item = suspend_platform_administrator(
                actor=request.user,
                user=target,
                rationale=serializer.validated_data["rationale"],
            )
        else:
            return Response({"action": ["Choose grant or suspend."]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(PlatformAdministratorSerializer(item).data)


class PlatformConfigurationView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        return Response(PlatformConfigurationSerializer(PlatformConfiguration.load()).data)

    def patch(self, request):  # type: ignore[no-untyped-def]
        serializer = PlatformConfigurationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        rationale = values.pop("rationale")
        item = update_platform_configuration(
            actor=request.user,
            values=values,
            rationale=rationale,
        )
        return Response(PlatformConfigurationSerializer(item).data)


class PlatformDemoRequestListView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        queryset = platform_demo_requests(
            status=request.query_params.get("status", ""),
            query=request.query_params.get("q", ""),
        )
        return Response(PlatformDemoRequestSerializer(queryset, many=True).data)


class PlatformDemoRequestStatusView(PlatformAdminBaseView):
    def post(self, request, demo_request_id):  # type: ignore[no-untyped-def]
        item = get_object_or_404(DemoRequest, id=demo_request_id)
        serializer = PlatformDemoRequestStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_demo_request_status(
            actor=request.user,
            demo_request=item,
            **serializer.validated_data,
        )
        return Response(PlatformDemoRequestSerializer(item).data)


class PlatformAuditListView(PlatformAdminBaseView):
    def get(self, request):  # type: ignore[no-untyped-def]
        queryset = platform_audit_events(
            query=request.query_params.get("q", ""),
            action=request.query_params.get("action", ""),
        )
        return Response(AuditEventSerializer(queryset[:250], many=True).data)
