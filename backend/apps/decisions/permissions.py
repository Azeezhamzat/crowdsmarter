"""DRF object permissions for decision endpoints."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from .models import Decision
from .policies import active_membership, can_edit_decision


class CanAccessDecision(BasePermission):
    """Allow active members to read and authorised actors to edit."""

    def has_object_permission(
        self, request: Request, view: object, obj: Decision
    ) -> bool:
        if request.method in SAFE_METHODS:
            return active_membership(actor=request.user, decision=obj) is not None
        return can_edit_decision(actor=request.user, decision=obj)
