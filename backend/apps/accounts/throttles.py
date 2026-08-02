"""Authentication-specific throttling."""

from rest_framework.throttling import AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limit repeated anonymous sign-in attempts by source address."""

    scope = "login"
