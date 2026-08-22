"""Passwordless applicant sign-in, cross-round application listing, and progress reports."""

from __future__ import annotations

import logging
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.db.models import Count, QuerySet
from django.utils import timezone

from apps.invitations.tokens import digest_token, generate_token
from apps.platform_admin.contact import notification_sender_email

from .models import ApplicantAccount, MagicLinkToken, ProgressReport

logger = logging.getLogger(__name__)

MAGIC_LINK_TTL_MINUTES = 30


class ApplicantServiceError(ValidationError):
    """Expected validation failure in an applicant identity workflow."""


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def build_magic_link_url(raw_token: str) -> str:
    base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base_url}/my-applications#token={quote(raw_token, safe='')}"


@transaction.atomic
def request_magic_link(*, email: str, name: str = "") -> tuple[ApplicantAccount, str]:
    """Get-or-create an applicant account by email and issue a fresh sign-in link."""
    normalised_email = _normalise_email(email)
    account = ApplicantAccount.objects.select_for_update().filter(email=normalised_email).first()
    if account is None:
        account = ApplicantAccount(email=normalised_email, name=name.strip())
        account.full_clean(validate_unique=False, validate_constraints=False)
        try:
            account.save()
        except IntegrityError as exc:
            raise ApplicantServiceError("Could not register that email.") from exc
    elif name.strip() and not account.name:
        account.name = name.strip()
        account.save(update_fields=["name", "updated_at"])

    raw_token = generate_token()
    token = MagicLinkToken(
        account=account,
        token_digest=digest_token(raw_token),
        expires_at=timezone.now() + timedelta(minutes=MAGIC_LINK_TTL_MINUTES),
    )
    token.save()
    return account, raw_token


def deliver_magic_link(*, account: ApplicantAccount, raw_token: str) -> str:
    """Send the sign-in email; returns 'sent' or 'failed'. Never blocks issuance."""
    link_url = build_magic_link_url(raw_token)
    try:
        delivered = send_mail(
            subject="Your CrowdSmarter applications link",
            message=(
                "Use this link to view every application you've submitted, across every "
                f"round:\n\n{link_url}\n\n"
                f"This link expires in {MAGIC_LINK_TTL_MINUTES} minutes and can only be used once."
            ),
            from_email=notification_sender_email(),
            recipient_list=[account.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception("Magic link delivery failed for applicant account %s", account.id)
        return "failed"
    return "sent" if delivered else "failed"


@transaction.atomic
def consume_magic_link(*, raw_token: str) -> tuple[ApplicantAccount, str]:
    """Verify and burn a magic link, returning the account and a fresh portal bearer token."""
    try:
        token = MagicLinkToken.objects.select_for_update().select_related("account").get(
            token_digest=digest_token(raw_token)
        )
    except MagicLinkToken.DoesNotExist as exc:
        raise PermissionDenied("This sign-in link is invalid.") from exc
    if token.consumed_at is not None:
        raise PermissionDenied("This sign-in link has already been used.")
    if token.expires_at <= timezone.now():
        raise PermissionDenied("This sign-in link has expired. Request a new one.")

    token.consumed_at = timezone.now()
    token.save(update_fields=["consumed_at", "updated_at"])

    account = token.account
    if account.email_verified_at is None:
        account.email_verified_at = timezone.now()

    raw_portal_token = generate_token()
    account.portal_token_digest = digest_token(raw_portal_token)
    account.save(update_fields=["email_verified_at", "portal_token_digest", "updated_at"])
    return account, raw_portal_token


def applicant_account_from_portal_token(*, raw_token: str) -> ApplicantAccount:
    try:
        return ApplicantAccount.objects.get(portal_token_digest=digest_token(raw_token))
    except ApplicantAccount.DoesNotExist as exc:
        raise PermissionDenied("Sign in again to view your applications.") from exc


def applications_for_account(*, account: ApplicantAccount) -> QuerySet:
    """Every idea submitted by a SessionParticipant linked to this account, across sessions."""
    from apps.ideation.models import Idea

    return (
        Idea.objects.filter(submitted_by_participant__account=account)
        .select_related("session", "session__organisation", "promoted_to_option")
        .order_by("-created_at")
    )


@transaction.atomic
def submit_progress_report(*, account: ApplicantAccount, idea, body: str) -> ProgressReport:
    """Record a post-award update against a funded application owned by this account."""
    from apps.ideation.models import Idea

    owned = Idea.objects.filter(id=idea.id, submitted_by_participant__account=account).exists()
    if not owned:
        raise PermissionDenied("This application does not belong to your account.")
    if not idea.promoted_to_option_id or idea.promoted_to_option.outcome_status != "funded":
        raise ApplicantServiceError("Progress reports can only be submitted for funded applications.")

    report = ProgressReport(idea=idea, account=account, body=body)
    report.full_clean(validate_unique=False, validate_constraints=False)
    report.save()
    return report


def progress_reports_for_idea(*, idea) -> QuerySet[ProgressReport]:
    return ProgressReport.objects.filter(idea=idea).select_related("account")
