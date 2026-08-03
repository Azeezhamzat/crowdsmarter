"""Thin REST endpoints for method governance."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .selectors import method_for_user, methods_for_organisation, usages_for_organisation, version_for_user
from .serializers import (
    DecisionMethodSerializer, MethodCloneSerializer, MethodCreateSerializer, MethodRetireSerializer,
    MethodUsageSerializer, MethodVersionSerializer, MethodVersionUpdateSerializer,
)
from .services import (
    approve_method_version, clone_builtin_method, create_method, create_method_version,
    retire_method, update_draft_version,
)


class OrganisationMethodListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = methods_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(DecisionMethodSerializer(items, many=True).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = MethodCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_method(actor=request.user, organisation=organisation, **serializer.validated_data)
        item = method_for_user(user=request.user, method_id=item.id)
        return Response(DecisionMethodSerializer(item).data, status=status.HTTP_201_CREATED)


class OrganisationMethodCloneView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = MethodCloneSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = clone_builtin_method(actor=request.user, organisation=organisation, **serializer.validated_data)
        item = method_for_user(user=request.user, method_id=item.id)
        return Response(DecisionMethodSerializer(item).data, status=status.HTTP_201_CREATED)


class DecisionMethodDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, method_id):  # type: ignore[no-untyped-def]
        return Response(DecisionMethodSerializer(method_for_user(user=request.user, method_id=method_id)).data)


class DecisionMethodNewVersionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, method_id):  # type: ignore[no-untyped-def]
        version = create_method_version(actor=request.user, method=method_for_user(user=request.user, method_id=method_id))
        return Response(MethodVersionSerializer(version).data, status=status.HTTP_201_CREATED)


class DecisionMethodVersionDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, version_id):  # type: ignore[no-untyped-def]
        return Response(
            MethodVersionSerializer(version_for_user(user=request.user, version_id=version_id)).data
        )

    def patch(self, request, version_id):  # type: ignore[no-untyped-def]
        version = version_for_user(user=request.user, version_id=version_id)
        serializer = MethodVersionUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        version = update_draft_version(actor=request.user, version=version, changes=dict(serializer.validated_data))
        return Response(MethodVersionSerializer(version).data)


class DecisionMethodVersionApproveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, version_id):  # type: ignore[no-untyped-def]
        version = approve_method_version(actor=request.user, version=version_for_user(user=request.user, version_id=version_id))
        return Response(MethodVersionSerializer(version).data)


class DecisionMethodRetireView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, method_id):  # type: ignore[no-untyped-def]
        serializer = MethodRetireSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = retire_method(
            actor=request.user,
            method=method_for_user(user=request.user, method_id=method_id),
            **serializer.validated_data,
        )
        return Response(DecisionMethodSerializer(method).data)


class OrganisationMethodUsageView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        items = usages_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(MethodUsageSerializer(items, many=True).data)
