"""Thin read-only portfolio endpoints."""

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.serializers import StrictSerializer
from apps.decisions.models import Decision

from .serializers import OrganisationPortfolioSerializer, PersonalWorkSerializer
from .services import organisation_portfolio, personal_work


class PortfolioFilterSerializer(StrictSerializer):
    status = serializers.ChoiceField(
        choices=Decision.Status.choices,
        required=False,
        allow_blank=True,
    )
    urgency = serializers.ChoiceField(
        choices=Decision.Urgency.choices,
        required=False,
        allow_blank=True,
    )
    workspace_id = serializers.UUIDField(required=False)
    owner_id = serializers.UUIDField(required=False)
    q = serializers.CharField(max_length=240, required=False, allow_blank=True)
    my_work = serializers.BooleanField(required=False, default=False)
    overdue = serializers.BooleanField(required=False, default=False)


class PersonalWorkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response(PersonalWorkSerializer(personal_work(user=request.user)).data)


class OrganisationPortfolioView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        serializer = PortfolioFilterSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        result = organisation_portfolio(
            user=request.user,
            organisation_id=organisation_id,
            status=values.get("status", ""),
            urgency=values.get("urgency", ""),
            workspace_id=values.get("workspace_id"),
            owner_id=values.get("owner_id"),
            query=values.get("q", ""),
            my_work=values.get("my_work", False),
            overdue_only=values.get("overdue", False),
        )
        return Response(
            OrganisationPortfolioSerializer(
                result, context={"request": request}
            ).data
        )
