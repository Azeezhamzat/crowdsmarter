"""Rate limits for invitation issuance and acceptance."""

from rest_framework.throttling import SimpleRateThrottle


class _ActorOrAddressThrottle(SimpleRateThrottle):
    """Use account identity when present and client address otherwise."""

    def get_cache_key(self, request, view):  # type: ignore[no-untyped-def]
        if request.user.is_authenticated:
            ident = f"user:{request.user.pk}"
        else:
            ident = f"ip:{self.get_ident(request)}"
        return self.cache_format % {"scope": self.scope, "ident": ident}


class InvitationManagementThrottle(_ActorOrAddressThrottle):
    """Limit repeated invitation management operations."""

    scope = "invitation_management"


class InvitationAcceptanceThrottle(_ActorOrAddressThrottle):
    """Limit repeated token probing and account creation attempts."""

    scope = "invitation_acceptance"
