"""User account model."""

import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.functions import Lower

from apps.core.models import UUIDTimeStampedModel

from .managers import UserManager


class User(AbstractUser):
    """A user identified by email instead of a public username."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None  # type: ignore[assignment]
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []  # type: ignore[misc]

    objects = UserManager()  # type: ignore[misc, assignment]

    class Meta:
        ordering = ["email"]
        constraints = [models.UniqueConstraint(Lower("email"), name="unique_user_email_ci")]

    def clean(self) -> None:
        """Normalise identity fields before validation and persistence."""
        super().clean()
        self.email = self.email.strip().lower()

    def __str__(self) -> str:
        return self.email


class TOTPDevice(UUIDTimeStampedModel):
    """One time-based one-time-password enrollment for a user's account.

    A row exists as soon as enrollment begins; `confirmed_at` is null until
    the user proves possession of the secret with a valid code, so an
    abandoned enrollment attempt never silently enables MFA.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="totp_device"
    )
    secret_encrypted = models.TextField()
    confirmed_at = models.DateTimeField(null=True, blank=True)

    @property
    def is_confirmed(self) -> bool:
        return self.confirmed_at is not None

    def __str__(self) -> str:
        return (
            f"TOTP device for {self.user.email} ({'confirmed' if self.is_confirmed else 'pending'})"
        )


class MFABackupCode(UUIDTimeStampedModel):
    """A single-use recovery code for when the authenticator app is unavailable.

    Only the keyed digest is stored, matching how invitation tokens are kept -
    the plaintext code is shown to the user exactly once, at generation time.
    """

    device = models.ForeignKey(TOTPDevice, on_delete=models.CASCADE, related_name="backup_codes")
    code_digest = models.CharField(max_length=64, unique=True)
    used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Backup code for {self.device.user.email} ({'used' if self.used_at else 'unused'})"


class EmailChangeRequest(UUIDTimeStampedModel):
    """A short-lived, single-use request to verify a replacement email address.

    The plaintext token is sent to the proposed address and never persisted.
    Keeping completion and invalidation separate makes account-security reviews
    distinguish successful changes from requests superseded by their owner.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_change_requests",
    )
    new_email = models.EmailField()
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "expires_at"], name="acct_email_user_exp_idx"),
        ]

    def __str__(self) -> str:
        if self.completed_at:
            state = "completed"
        elif self.invalidated_at:
            state = "invalidated"
        else:
            state = "pending"
        return f"Email change for {self.user.email} to {self.new_email} ({state})"
