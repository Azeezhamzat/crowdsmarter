"""Platform-level permission primitives."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import BasePermission

from .models import PlatformAdministrator


def is_platform_administrator(user: Any) -> bool:
    if not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    cached = getattr(user, "_crowdsmarter_platform_admin", None)
    if cached is not None:
        return bool(cached)
    value = PlatformAdministrator.objects.filter(
        user=user,
        status=PlatformAdministrator.Status.ACTIVE,
    ).exists()
    user._crowdsmarter_platform_admin = value
    return value


class IsPlatformAdministrator(BasePermission):
    message = "An active CrowdSmarter platform-administrator capability is required."

    def has_permission(self, request, view):  # type: ignore[no-untyped-def]
        return is_platform_administrator(request.user)
