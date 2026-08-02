"""Read-only tenant audit API."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .selectors import audit_events_for_organisation
from .serializers import AuditEventSerializer


class OrganisationAuditEventListView(APIView):
    """List recent attributable changes for an organisation manager."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        action = request.query_params.get("action", "").strip()
        object_type = request.query_params.get("object_type", "").strip()
        events = audit_events_for_organisation(
            user=request.user,
            organisation_id=organisation_id,
            action=action,
            object_type=object_type,
        )[:100]
        return Response(AuditEventSerializer(events, many=True).data)
