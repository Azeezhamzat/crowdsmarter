"""Account self-service workflows."""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.text import slugify

from apps.audit.services import record_event
from apps.organisations.models import Organisation
from apps.platform_admin.contact import notification_sender_email

from . import totp
from .models import MFABackupCode, TOTPDevice

User = get_user_model()

_BACKUP_CODE_COUNT = 10
_BACKUP_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I ambiguity


class MFAServiceError(ValidationError):
    """Expected MFA workflow failure."""


class SignupServiceError(ValidationError):
    """Expected self-serve signup failure."""


def _unique_organisation_slug(*, name: str) -> str:
    base = slugify(name)[:70] or "commons"
    candidate = base
    suffix = 1
    while Organisation.objects.filter(slug=candidate).exists():
        suffix += 1
        candidate = f"{base}-{suffix}"
    return candidate


@transaction.atomic
def sign_up(
    *,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    organisation_name: str,
) -> tuple[User, Organisation]:
    """Create a new self-serve account and its first, owned commons.

    This is the free, no-invitation entry point: anyone can start their own
    commons without an existing organisation vouching for them. It reuses the
    same ``create_organisation`` service every authenticated "new organisation"
    action already goes through, so the new tenant gets the same default
    workspace and subscription record as any other.
    """
    normalised_email = email.strip().lower()
    if User.objects.filter(email__iexact=normalised_email).exists():
        raise SignupServiceError(
            {"email": "An account already exists for this email. Sign in instead."}
        )
    candidate = User(email=normalised_email, first_name=first_name.strip(), last_name=last_name.strip())
    validate_password(password, user=candidate)
    user = User.objects.create_user(
        email=normalised_email,
        password=password,
        first_name=candidate.first_name,
        last_name=candidate.last_name,
    )

    from apps.organisations.services import create_organisation

    organisation = create_organisation(
        actor=user,
        name=organisation_name.strip(),
        slug=_unique_organisation_slug(name=organisation_name),
    )
    record_event(
        action="account.signed_up",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=user,
        organisation=organisation,
        metadata={"organisation_id": str(organisation.id)},
    )
    return user, organisation


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


def _digest_backup_code(normalised_code: str) -> str:
    """Keyed digest matching the invitation-token pattern: never store the raw code."""
    return hmac.new(
        key=settings.SECRET_KEY.encode("utf-8"),
        msg=normalised_code.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()


def normalise_backup_code(code: str) -> str:
    """Strip formatting so 'ab12-cd34', 'AB12CD34', and 'ab12 cd34' are equivalent."""
    return code.strip().upper().replace("-", "").replace(" ", "")


def _generate_backup_codes() -> list[str]:
    return [
        "".join(secrets.choice(_BACKUP_CODE_ALPHABET) for _ in range(8))
        for _ in range(_BACKUP_CODE_COUNT)
    ]


def _format_backup_code(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"


@dataclass(frozen=True)
class MFAEnrollment:
    """The secret and provisioning URI for a pending, unconfirmed enrollment."""

    secret: str
    provisioning_uri: str


@transaction.atomic
def begin_mfa_enrollment(*, user: User) -> MFAEnrollment:
    """Start (or restart) an MFA enrollment, replacing any unconfirmed attempt.

    A fresh secret is issued every time this is called so an abandoned or
    possibly-exposed pending secret can never be silently reused.
    """
    existing = TOTPDevice.objects.select_for_update().filter(user=user).first()
    if existing and existing.is_confirmed:
        raise MFAServiceError("Two-factor authentication is already enabled.")
    secret = totp.generate_secret()
    if existing:
        existing.secret = secret
        existing.save(update_fields=["secret", "updated_at"])
    else:
        TOTPDevice.objects.create(user=user, secret=secret)
    record_event(
        action="account.mfa_enrollment_started",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=user,
    )
    return MFAEnrollment(
        secret=secret,
        provisioning_uri=totp.provisioning_uri(secret=secret, email=user.email),
    )


@transaction.atomic
def confirm_mfa_enrollment(*, user: User, code: str) -> list[str]:
    """Verify the enrollment code and return newly generated backup codes.

    The plaintext codes are returned only here, once; afterwards only their
    keyed digests exist, the same one-time-reveal pattern used elsewhere for
    secrets that must never be recoverable after issuance.
    """
    try:
        device = TOTPDevice.objects.select_for_update().get(user=user)
    except TOTPDevice.DoesNotExist as exc:
        raise MFAServiceError("Start enrollment before confirming a code.") from exc
    if device.is_confirmed:
        raise MFAServiceError("Two-factor authentication is already enabled.")
    if not totp.verify_totp(secret=device.secret, code=code):
        raise MFAServiceError({"code": "That code is incorrect or has expired."})
    device.confirmed_at = timezone.now()
    device.save(update_fields=["confirmed_at", "updated_at"])
    plaintext_codes = _generate_backup_codes()
    MFABackupCode.objects.bulk_create(
        MFABackupCode(device=device, code_digest=_digest_backup_code(raw))
        for raw in plaintext_codes
    )
    record_event(
        action="account.mfa_enabled",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=user,
        metadata={"backup_code_count": len(plaintext_codes)},
    )
    return [_format_backup_code(raw) for raw in plaintext_codes]


@transaction.atomic
def disable_mfa(*, user: User) -> None:
    device = TOTPDevice.objects.select_for_update().filter(user=user).first()
    if device is None or not device.is_confirmed:
        raise MFAServiceError("Two-factor authentication is not enabled.")
    device.delete()
    record_event(
        action="account.mfa_disabled",
        object_type="accounts.User",
        object_id=str(user.id),
        actor=user,
    )


@transaction.atomic
def verify_mfa_code(*, user: User, code: str) -> bool:
    """Accept a live TOTP code, or consume an unused backup code as a fallback."""
    try:
        device = TOTPDevice.objects.select_for_update().get(
            user=user, confirmed_at__isnull=False
        )
    except TOTPDevice.DoesNotExist:
        return False
    if totp.verify_totp(secret=device.secret, code=code):
        return True
    digest = _digest_backup_code(normalise_backup_code(code))
    updated = MFABackupCode.objects.filter(
        device=device, code_digest=digest, used_at__isnull=True
    ).update(used_at=timezone.now())
    if updated:
        record_event(
            action="account.mfa_backup_code_used",
            object_type="accounts.User",
            object_id=str(user.id),
            actor=user,
        )
    return updated > 0


def mfa_is_enabled(*, user: User) -> bool:
    return TOTPDevice.objects.filter(user=user, confirmed_at__isnull=False).exists()
