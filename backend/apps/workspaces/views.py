"""Thin REST endpoints for workspace workflows."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organisations.selectors import organisation_for_user

from .permissions import CanAccessWorkspace
from .selectors import workspace_for_user, workspaces_for_organisation
from .serializers import (
    WorkspaceCreateSerializer,
    WorkspaceSerializer,
    WorkspaceUpdateSerializer,
)
from .services import create_workspace, update_workspace


class WorkspaceListCreateView(APIView):
    """List tenant workspaces or create one as a tenant manager."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        workspaces = workspaces_for_organisation(user=request.user, organisation_id=organisation_id)
        return Response(
            WorkspaceSerializer(workspaces, many=True, context={"request": request}).data
        )

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = WorkspaceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = create_workspace(
            actor=request.user,
            organisation=organisation,
            **serializer.validated_data,
        )
        return Response(
            WorkspaceSerializer(workspace, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class WorkspaceDetailView(APIView):
    """Read or update one tenant-scoped workspace."""

    permission_classes = [IsAuthenticated, CanAccessWorkspace]

    def _get_object(self, request, workspace_id):  # type: ignore[no-untyped-def]
        workspace = workspace_for_user(user=request.user, workspace_id=workspace_id)
        self.check_object_permissions(request, workspace)
        return workspace

    def get(self, request, workspace_id):  # type: ignore[no-untyped-def]
        workspace = self._get_object(request, workspace_id)
        return Response(WorkspaceSerializer(workspace, context={"request": request}).data)

    def patch(self, request, workspace_id):  # type: ignore[no-untyped-def]
        workspace = self._get_object(request, workspace_id)
        serializer = WorkspaceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workspace = update_workspace(
            actor=request.user,
            workspace=workspace,
            **serializer.validated_data,
        )
        return Response(WorkspaceSerializer(workspace, context={"request": request}).data)
