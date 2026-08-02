"""Object-level option permissions."""

from rest_framework.permissions import BasePermission

from apps.decisions.reasoning_policies import can_edit_reasoning


class CanEditDecisionOption(BasePermission):
    """Allow writes only through the structured reasoning policy."""

    def has_object_permission(self, request, view, obj):  # type: ignore[no-untyped-def]
        if request.method in {"GET", "HEAD", "OPTIONS"}:
            return True
        return can_edit_reasoning(
            actor=request.user,
            decision=obj.decision,
            created_by_id=obj.created_by_id,
        )
