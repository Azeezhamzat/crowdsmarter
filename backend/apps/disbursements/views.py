"""Organisation-scoped disbursement configuration and per-option payout endpoints."""

from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decision_options.selectors import option_for_user
from apps.organisations.selectors import organisation_for_user

from . import services
from .serializers import (
    DisbursementConfigurationSerializer,
    DisbursementSerializer,
    IssueDisbursementSerializer,
    SetDisbursementApiKeySerializer,
    SetDisbursementProviderSerializer,
)


class DisbursementConfigurationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        config = services.configuration_for_organisation(organisation=organisation)
        return Response(DisbursementConfigurationSerializer(config).data)

    def put(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SetDisbursementProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = services.set_disbursement_provider(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(DisbursementConfigurationSerializer(config).data)


class DisbursementApiKeyView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SetDisbursementApiKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = services.set_disbursement_api_key(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(DisbursementConfigurationSerializer(config).data)

    def delete(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        config = services.clear_disbursement_api_key(actor=request.user, organisation=organisation)
        return Response(DisbursementConfigurationSerializer(config).data)


class DisbursementConnectionTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        return Response(
            services.test_disbursement_connection(actor=request.user, organisation=organisation)
        )


class OptionDisbursementListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, option_id):
        option = option_for_user(user=request.user, option_id=option_id)
        items = services.disbursements_for_option(option=option)
        return Response(DisbursementSerializer(items, many=True).data)

    def post(self, request, option_id):
        option = option_for_user(user=request.user, option_id=option_id)
        serializer = IssueDisbursementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = services.issue_disbursement(
            actor=request.user, option=option, **serializer.validated_data
        )
        return Response(DisbursementSerializer(item).data, status=status.HTTP_201_CREATED)
