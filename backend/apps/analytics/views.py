"""Tenant-safe analytics endpoint."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .services import organisation_analytics


class OrganisationAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(
            user=request.user,
            organisation_id=organisation_id,
        )
        return Response(organisation_analytics(organisation=organisation))
