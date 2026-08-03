"""Thin endpoints for plan entitlements and subscriptions."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .selectors import active_plans, subscription_for_user
from .serializers import (
    ChangePlanSerializer,
    OrganisationSubscriptionSerializer,
    PlanSerializer,
    SetBillingContactSerializer,
)
from .services import change_plan, set_billing_contact


class PlanListView(APIView):
    """The proposed packaging tiers available for self-service selection."""

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response(PlanSerializer(active_plans(), many=True).data)


class OrganisationSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        subscription = subscription_for_user(user=request.user, organisation_id=organisation_id)
        return Response(OrganisationSubscriptionSerializer(subscription).data)


class ChangePlanView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = ChangePlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = change_plan(
            actor=request.user, organisation=organisation, **serializer.validated_data
        )
        return Response(OrganisationSubscriptionSerializer(subscription).data)


class SetBillingContactView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = SetBillingContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subscription = set_billing_contact(
            actor=request.user,
            organisation=organisation,
            user_id=serializer.validated_data.get("user_id"),
        )
        return Response(OrganisationSubscriptionSerializer(subscription).data)
