"""Organisation-scoped lookup configuration and applicant-verification endpoints."""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from . import services
from .serializers import (
    LookupConfigurationSerializer,
    LookupOrganisationQuerySerializer,
    SetLookupApiKeySerializer,
    SetLookupProviderSerializer,
)


class LookupConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        config = services.configuration_for_organisation(organisation=organisation)
        return Response(LookupConfigurationSerializer(config).data)

    def put(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SetLookupProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = services.set_lookup_provider(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(LookupConfigurationSerializer(config).data)


class LookupApiKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SetLookupApiKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = services.set_lookup_api_key(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(LookupConfigurationSerializer(config).data)

    def delete(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        config = services.clear_lookup_api_key(actor=request.user, organisation=organisation)
        return Response(LookupConfigurationSerializer(config).data)


class LookupConnectionTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        return Response(
            services.test_lookup_connection(actor=request.user, organisation=organisation)
        )


class LookupOrganisationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = LookupOrganisationQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = services.lookup_organisation(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(result)
