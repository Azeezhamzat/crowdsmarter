"""DRF object permissions for participant endpoints."""

from typing import Any, cast

from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from apps.decisions.policies import active_membership, can_manage_participants

from .models import Participant


class CanAccessParticipant(BasePermission):
    """Allow tenant reads and authorised participant management."""

    def has_object_permission(self, request: Request, view: object, obj: Participant) -> bool:
        actor = cast(Any, request.user)
        if request.method in SAFE_METHODS:
            return active_membership(actor=actor, decision=obj.decision) is not None
        return can_manage_participants(actor=actor, decision=obj.decision)
