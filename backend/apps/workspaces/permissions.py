"""DRF object permissions for workspace endpoints."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from .models import Workspace
from .policies import active_membership, can_manage_workspace


class CanAccessWorkspace(BasePermission):
    """Allow active members to read and managers to modify a workspace."""

    def has_object_permission(
        self, request: Request, view: object, obj: Workspace
    ) -> bool:
        if request.method in SAFE_METHODS:
            return active_membership(actor=request.user, workspace=obj) is not None
        return can_manage_workspace(actor=request.user, workspace=obj)
