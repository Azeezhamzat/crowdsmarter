"""DRF object permissions for participant endpoints."""

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from apps.decisions.policies import active_membership, can_manage_participants

from .models import Participant


class CanAccessParticipant(BasePermission):
    """Allow tenant reads and authorised participant management."""

    def has_object_permission(
        self, request: Request, view: object, obj: Participant
    ) -> bool:
        if request.method in SAFE_METHODS:
            return active_membership(actor=request.user, decision=obj.decision) is not None
        return can_manage_participants(actor=request.user, decision=obj.decision)
