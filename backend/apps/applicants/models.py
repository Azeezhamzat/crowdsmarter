"""A persistent, passwordless identity for people who apply across multiple rounds.

Deliberately lighter-weight than apps.accounts.User (no password, no MFA) and
distinct from apps.ideation.SessionParticipant (which stays scoped per-session
for anonymous/one-off participation). An ApplicantAccount is the thing that
lets the same person's applications be found across sessions once they choose
to verify an email once.
"""

from __future__ import annotations

from django.db import models
from django.db.models.functions import Lower

from apps.core.models import UUIDTimeStampedModel


class ApplicantAccount(UUIDTimeStampedModel):
    email = models.EmailField()
    name = models.CharField(max_length=200, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)
    portal_token_digest = models.CharField(max_length=64, unique=True, null=True, blank=True)
    portal_token_expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["email"]
        constraints = [
            models.UniqueConstraint(Lower("email"), name="unique_applicant_account_email_ci"),
            models.CheckConstraint(
                condition=~models.Q(email=""), name="applicant_account_email_not_empty"
            ),
        ]

    def clean(self) -> None:
        super().clean()
        self.email = self.email.strip().lower()
        self.name = self.name.strip()

    @property
    def is_verified(self) -> bool:
        return self.email_verified_at is not None

    def __str__(self) -> str:
        return self.email


class MagicLinkToken(UUIDTimeStampedModel):
    """A single-use, expiring bearer token for passwordless applicant sign-in.

    Only the keyed digest is stored, matching apps.invitations.tokens - the
    raw token exists only in the email body and the momentary request.
    """

    account = models.ForeignKey(
        ApplicantAccount, on_delete=models.CASCADE, related_name="magic_links"
    )
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "id"]
        indexes = [
            models.Index(fields=["account", "-created_at"], name="magic_link_account_created_idx"),
        ]

    def __str__(self) -> str:
        return f"Magic link for {self.account.email}"


class ProgressReport(UUIDTimeStampedModel):
    """A post-award update a grantee submits against their funded application."""

    idea = models.ForeignKey(
        "ideation.Idea", on_delete=models.CASCADE, related_name="progress_reports"
    )
    account = models.ForeignKey(
        ApplicantAccount, on_delete=models.PROTECT, related_name="progress_reports"
    )
    body = models.TextField()

    class Meta:
        ordering = ["-created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(body=""), name="progress_report_body_not_empty"
            ),
        ]
        indexes = [
            models.Index(fields=["idea", "-created_at"], name="progress_report_idea_idx"),
        ]

    def clean(self) -> None:
        super().clean()
        self.body = self.body.strip()

    def __str__(self) -> str:
        return f"Progress report on {self.idea.title} by {self.account.email}"
