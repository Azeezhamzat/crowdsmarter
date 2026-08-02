"""Authentication-specific throttling."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limit repeated anonymous sign-in attempts by source address."""

    scope = "login"


class PasswordResetRequestThrottle(AnonRateThrottle):
    """Limit anonymous password-recovery requests by source address."""

    scope = "password_reset_request"


class PasswordResetConfirmThrottle(AnonRateThrottle):
    """Limit reset-token validation attempts by source address."""

    scope = "password_reset_confirm"


class AccountSecurityThrottle(UserRateThrottle):
    """Limit sensitive authenticated account changes."""

    scope = "account_security"
