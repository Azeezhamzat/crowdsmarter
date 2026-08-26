"""Authentication-specific throttling."""

from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """Limit repeated anonymous sign-in attempts by source address."""

    scope = "login"


class SignupThrottle(AnonRateThrottle):
    """Limit anonymous self-serve account creation by source address."""

    scope = "signup"


class PasswordResetRequestThrottle(AnonRateThrottle):
    """Limit anonymous password-recovery requests by source address."""

    scope = "password_reset_request"


class PasswordResetConfirmThrottle(AnonRateThrottle):
    """Limit reset-token validation attempts by source address."""

    scope = "password_reset_confirm"


class AccountSecurityThrottle(UserRateThrottle):
    """Limit sensitive authenticated account changes."""

    scope = "account_security"


class MFAVerifyThrottle(AnonRateThrottle):
    """Limit two-factor code guesses during login by source address.

    Anonymous (not user-scoped): at this point in the flow the request has
    not been logged in yet, so there is no authenticated user to key on.
    """

    scope = "mfa_verify"
