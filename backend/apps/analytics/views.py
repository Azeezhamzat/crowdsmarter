"""Tenant-safe analytics endpoints."""

from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.organisations.models import Membership
from apps.organisations.selectors import organisation_for_user

from .services import organisation_analytics, organisation_analytics_insight


class OrganisationAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(
            user=request.user,
            organisation_id=organisation_id,
        )
        return Response(organisation_analytics(organisation=organisation))


class OrganisationAnalyticsInsightView(APIView):
    """Owner/admin-triggered AI narrative over the same metrics, generated on demand."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "analytics_insights"

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(
            user=request.user,
            organisation_id=organisation_id,
        )
        membership = organisation.memberships.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
        ).first()
        if membership is None or membership.role not in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }:
            raise PermissionDenied(
                "Only organisation owners and administrators can generate AI analytics insights."
            )
        return Response(organisation_analytics_insight(organisation=organisation))
