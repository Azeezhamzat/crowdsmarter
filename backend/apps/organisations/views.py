"""Thin REST endpoints for organisation workflows."""

from django.db.models import Prefetch
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership
from .permissions import CanManageMembership, CanManageOrganisation, IsOrganisationMember
from .selectors import (
    deletion_request_for_user,
    deletion_requests_for_organisation,
    membership_events_for_organisation,
    membership_for_user,
    memberships_for_user_organisation,
    organisation_for_user,
    organisations_for_user,
)
from .serializers import (
    MembershipEventSerializer,
    MembershipSerializer,
    MembershipUpdateSerializer,
    OrganisationAdministrationUpdateSerializer,
    OrganisationCreateSerializer,
    OrganisationDeletionRequestSerializer,
    OrganisationSerializer,
    OrganisationStateChangeSerializer,
    OrganisationUpdateSerializer,
    OwnershipTransferSerializer,
)
from .services import (
    cancel_organisation_deletion,
    change_membership_role,
    create_organisation,
    deactivate_organisation,
    reactivate_organisation,
    remove_membership,
    request_organisation_deletion,
    transfer_organisation_ownership,
    update_organisation,
    update_organisation_administration,
)



class OrganisationListCreateView(APIView):
    """List visible organisations or create a new tenant."""

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        active_memberships = Membership.objects.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
        )
        queryset = organisations_for_user(request.user).prefetch_related(
            Prefetch(
                "memberships",
                queryset=active_memberships,
                to_attr="prefetched_active_memberships",
            )
        )
        data = OrganisationSerializer(
            queryset, many=True, context={"request": request}
        ).data
        return Response(data)

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = OrganisationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = create_organisation(actor=request.user, **serializer.validated_data)
        return Response(
            OrganisationSerializer(organisation, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class OrganisationDetailView(APIView):
    """Read or update one tenant without cross-tenant disclosure."""

    permission_classes = [IsAuthenticated, CanManageOrganisation]

    def _get_object(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        self.check_object_permissions(request, organisation)
        return organisation

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = self._get_object(request, organisation_id)
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)

    def patch(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = self._get_object(request, organisation_id)
        serializer = OrganisationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = update_organisation(
            actor=request.user,
            organisation=organisation,
            **serializer.validated_data,
        )
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)


class MembershipListView(APIView):
    """List tenant memberships. New access begins through invitation acceptance."""

    permission_classes = [IsAuthenticated, IsOrganisationMember]

    def _get_organisation(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        self.check_object_permissions(request, organisation)
        return organisation

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        self._get_organisation(request, organisation_id)
        memberships = memberships_for_user_organisation(
            user=request.user, organisation_id=organisation_id
        )
        return Response(MembershipSerializer(memberships, many=True).data)


class MembershipDetailView(APIView):
    """Change or remove one membership under object-level rules."""

    permission_classes = [IsAuthenticated, CanManageMembership]

    def _get_object(self, request, membership_id):  # type: ignore[no-untyped-def]
        membership = membership_for_user(user=request.user, membership_id=membership_id)
        self.check_object_permissions(request, membership)
        return membership

    def patch(self, request, membership_id):  # type: ignore[no-untyped-def]
        membership = self._get_object(request, membership_id)
        serializer = MembershipUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = change_membership_role(
            actor=request.user,
            membership=membership,
            role=serializer.validated_data["role"],
        )
        return Response(MembershipSerializer(membership).data)

    def delete(self, request, membership_id):  # type: ignore[no-untyped-def]
        membership = self._get_object(request, membership_id)
        remove_membership(actor=request.user, membership=membership)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganisationAdministrationView(APIView):
    """Read or update organisation profile and administrative policy."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)

    def patch(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OrganisationAdministrationUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = update_organisation_administration(
            actor=request.user, organisation=organisation, changes=dict(serializer.validated_data)
        )
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)


class OrganisationOwnershipTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OwnershipTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target = membership_for_user(
            user=request.user, membership_id=serializer.validated_data["target_membership_id"]
        )
        if target.organisation_id != organisation.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"target_membership_id": "Choose a member of this organisation."})
        previous, new = transfer_organisation_ownership(
            actor=request.user, organisation=organisation, target_membership=target,
            rationale=serializer.validated_data["rationale"],
        )
        return Response({"previous_owner": MembershipSerializer(previous).data, "new_owner": MembershipSerializer(new).data})


class OrganisationMembershipHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        membership = organisation.memberships.filter(user=request.user, status=Membership.Status.ACTIVE).first()
        if membership is None or membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("This history requires an owner or administrator role.")
        items = membership_events_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(MembershipEventSerializer(items, many=True).data)


class OrganisationDeactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OrganisationStateChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = deactivate_organisation(
            actor=request.user, organisation=organisation,
            confirmation=serializer.validated_data.get("confirmation", ""),
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)


class OrganisationReactivateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OrganisationStateChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organisation = reactivate_organisation(
            actor=request.user, organisation=organisation,
            rationale=serializer.validated_data.get("rationale", ""),
        )
        return Response(OrganisationSerializer(organisation, context={"request": request}).data)


class OrganisationDeletionRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        membership = organisation.memberships.filter(
            user=request.user, status=Membership.Status.ACTIVE, role=Membership.Role.OWNER
        ).first()
        if membership is None:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Only an organisation owner may view deletion requests.")
        items = deletion_requests_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(OrganisationDeletionRequestSerializer(items, many=True).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OrganisationStateChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = request_organisation_deletion(
            actor=request.user, organisation=organisation,
            confirmation=serializer.validated_data.get("confirmation", ""),
            reason=serializer.validated_data.get("reason", ""),
        )
        return Response(OrganisationDeletionRequestSerializer(item).data, status=status.HTTP_201_CREATED)


class OrganisationDeletionRequestCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):  # type: ignore[no-untyped-def]
        serializer = OrganisationStateChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = cancel_organisation_deletion(
            actor=request.user,
            deletion_request=deletion_request_for_user(user=request.user, request_id=request_id),
            rationale=serializer.validated_data.get("rationale", ""),
        )
        return Response(OrganisationDeletionRequestSerializer(item).data)
