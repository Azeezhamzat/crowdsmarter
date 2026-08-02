"""Permission-checked customer export endpoints."""

from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.audit.services import record_event
from apps.decisions.selectors import decision_for_user
from apps.organisations.models import Membership
from apps.organisations.selectors import organisation_for_user

from .services import build_decision_export, build_organisation_export
from .throttles import ExportRateThrottle


def _zip_response(*, filename: str, content: bytes) -> HttpResponse:
    response = HttpResponse(content, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response["Cache-Control"] = "private, no-store"
    response["X-Content-Type-Options"] = "nosniff"
    return response


class OrganisationExportView(APIView):
    """Download a complete organisation archive as an owner or administrator."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ExportRateThrottle]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        membership = organisation.memberships.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
        ).first()
        if membership is None or membership.role not in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Only organisation owners and administrators can export all tenant data.")
        archive = build_organisation_export(organisation=organisation)
        record_event(
            action="organisation.export_downloaded",
            object_type="organisations.Organisation",
            object_id=str(organisation.id),
            actor=request.user,
            organisation=organisation,
            metadata={"filename": archive.filename, "schema_version": "1.0"},
        )
        return _zip_response(filename=archive.filename, content=archive.content)


class DecisionExportView(APIView):
    """Download a portable dossier for one visible decision."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ExportRateThrottle]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        archive = build_decision_export(decision=decision)
        record_event(
            action="decision.export_downloaded",
            object_type="decisions.Decision",
            object_id=str(decision.id),
            actor=request.user,
            organisation=decision.organisation,
            metadata={"filename": archive.filename, "schema_version": "1.0"},
        )
        return _zip_response(filename=archive.filename, content=archive.content)
