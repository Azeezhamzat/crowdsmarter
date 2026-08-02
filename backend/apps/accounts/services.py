"""Account self-service workflows."""

from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from apps.audit.services import record_event
from apps.platform_admin.contact import notification_sender_email

User = get_user_model()


@dataclass(frozen=True)
class PasswordResetDispatch:
    """Outcome of a password-recovery request without exposing account existence."""

    delivered: bool
    development_url: str | None = None


def _reset_url(user: User) -> str:
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    base_url = settings.FRONTEND_BASE_URL.rstrip("/")
    return f"{base_url}/reset-password#uid={uid}&token={token}"


def request_password_reset(*, email: str) -> PasswordResetDispatch:
    """Send a password-reset link when an active account exists.

    Callers must always return the same public response so this workflow cannot
    be used to enumerate registered email addresses.
    """

    normalised_email = email.strip().lower()
    user = User.objects.filter(email__iexact=normalised_email, is_active=True).first()
    if user is None:
        return PasswordResetDispatch(delivered=False)

    reset_url = _reset_url(user)
    delivered_count = send_mail(
        subject="Reset your CrowdSmarter password",
        message=(
            "A password reset was requested for your CrowdSmarter account.\n\n"
            f"Open this link to choose a new password:\n{reset_url}\n\n"
            "If you did not request this, no action is required. The link becomes "
            "invalid after your password changes or the configured reset window expires."
        ),
        from_email=notification_sender_email(),
        recipient_list=[user.email],
        fail_silently=True,
    )
    record_event(
        action="account.password_reset_requested",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=None,
        metadata={"delivery_succeeded": delivered_count > 0},
    )
    development_url = reset_url if settings.DEBUG else None
    return PasswordResetDispatch(
        delivered=delivered_count > 0,
        development_url=development_url,
    )


@transaction.atomic
def update_profile(*, user: User, first_name: str, last_name: str) -> User:
    """Update editable personal profile fields and audit the change."""

    user.first_name = first_name.strip()
    user.last_name = last_name.strip()
    user.full_clean(exclude=["password"])
    user.save(update_fields=["first_name", "last_name"])
    record_event(
        action="account.profile_updated",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=user,
        metadata={"first_name": user.first_name, "last_name": user.last_name},
    )
    return user


@transaction.atomic
def set_new_password(*, user: User, new_password: str, actor: User | None) -> None:
    """Set a new password and append an account-security audit event."""

    user.set_password(new_password)
    user.save(update_fields=["password"])
    record_event(
        action="account.password_changed" if actor else "account.password_reset_completed",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=actor,
    )
