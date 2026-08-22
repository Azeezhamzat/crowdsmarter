"""Transactional invitation, delivery, and acceptance workflows."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, models, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from apps.accounts.models import User
from apps.audit.services import record_event
from apps.platform_admin.contact import notification_sender_email
from apps.notifications.models import Notification
from apps.notifications.services import create_notification
from apps.organisations.models import Membership, MembershipEvent, Organisation

from .models import OrganisationInvitation
from .tokens import digest_token, generate_token

logger = logging.getLogger(__name__)


class InvitationServiceError(ValidationError):
    """Expected validation failure in an invitation workflow."""


@dataclass(frozen=True)
class InvitationDelivery:
    """Outcome of one best-effort invitation email delivery."""

    status: str
    acceptance_url: str | None


def _normalise_email(email: str) -> str:
    return email.strip().lower()


def _expiry_time():
    hours = int(getattr(settings, "INVITATION_EXPIRY_HOURS", 168))
    return timezone.now() + timedelta(hours=hours)


def _manager_membership(*, actor: User, organisation: Organisation) -> Membership:
    try:
        membership = Membership.objects.select_for_update().get(
            organisation=organisation,
            user=actor,
            status=Membership.Status.ACTIVE,
        )
    except Membership.DoesNotExist as exc:
        raise PermissionDenied("You are not an active member of this organisation.") from exc
    if membership.role not in {Membership.Role.OWNER, Membership.Role.ADMIN}:
        raise PermissionDenied("This action requires an owner or administrator role.")
    if organisation.status != Organisation.Status.ACTIVE:
        raise InvitationServiceError("Reactivate the organisation before managing invitations.")
    if (
        organisation.invitation_policy == Organisation.InvitationPolicy.OWNERS_ONLY
        and membership.role != Membership.Role.OWNER
    ):
        raise PermissionDenied("This organisation allows only owners to manage invitations.")
    return membership


def _validate_assignable_role(*, actor_membership: Membership, role: str) -> None:
    valid_roles = {value for value, _ in Membership.Role.choices}
    if role not in valid_roles:
        raise InvitationServiceError("Select a valid organisation role.")
    if role == Membership.Role.OWNER and actor_membership.role != Membership.Role.OWNER:
        raise PermissionDenied("Only an owner may invite another owner.")


def effective_status(invitation: OrganisationInvitation) -> str:
    """Return the public status, including time-derived expiry."""
    if (
        invitation.status == OrganisationInvitation.Status.PENDING
        and invitation.expires_at <= timezone.now()
    ):
        return "expired"
    return invitation.status


def build_acceptance_url(raw_token: str) -> str:
    """Build the provider-neutral browser URL included in invitation email."""
    base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
    return f"{base_url}/accept-invitation#token={quote(raw_token, safe='')}"


@transaction.atomic
def create_invitation(
    *,
    actor: User,
    organisation: Organisation,
    email: str,
    role: str,
) -> tuple[OrganisationInvitation, str]:
    """Create or reissue an invitation after explicit manager authorisation."""
    actor_membership = _manager_membership(actor=actor, organisation=organisation)
    _validate_assignable_role(actor_membership=actor_membership, role=role)
    normalised_email = _normalise_email(email)

    if Membership.objects.filter(
        organisation=organisation,
        user__email__iexact=normalised_email,
    ).exists():
        raise InvitationServiceError("That person is already a member of this organisation.")

    invitation = OrganisationInvitation.objects.select_for_update().filter(
        organisation=organisation,
        email=normalised_email,
    ).first()
    if (
        invitation is not None
        and invitation.status == OrganisationInvitation.Status.PENDING
        and invitation.expires_at > timezone.now()
    ):
        raise InvitationServiceError(
            "A pending invitation already exists for this email. Resend or revoke it instead."
        )

    raw_token = generate_token()
    token_digest = digest_token(raw_token)
    now = timezone.now()
    action = "invitation.created"

    if invitation is None:
        invitation = OrganisationInvitation(
            organisation=organisation,
            email=normalised_email,
            role=role,
            status=OrganisationInvitation.Status.PENDING,
            token_digest=token_digest,
            invited_by=actor,
            expires_at=_expiry_time(),
        )
    else:
        action = "invitation.reissued"
        invitation.role = role
        invitation.status = OrganisationInvitation.Status.PENDING
        invitation.token_digest = token_digest
        invitation.invited_by = actor
        invitation.expires_at = _expiry_time()
        invitation.accepted_by = None
        invitation.accepted_at = None
        invitation.revoked_at = None
        invitation.last_sent_at = None
        invitation.send_count = 0

    invitation.full_clean(validate_unique=False, validate_constraints=False)
    try:
        invitation.save()
    except IntegrityError as exc:
        raise InvitationServiceError("The invitation could not be created safely.") from exc

    record_event(
        action=action,
        object_type="organisation_invitation",
        object_id=str(invitation.id),
        actor=actor,
        organisation=organisation,
        metadata={
            "email": invitation.email,
            "role": invitation.role,
            "expires_at": invitation.expires_at,
            "issued_at": now,
        },
    )
    return invitation, raw_token


@transaction.atomic
def rotate_invitation(
    *,
    actor: User,
    invitation: OrganisationInvitation,
) -> tuple[OrganisationInvitation, str]:
    """Rotate the secret and extend expiry for a pending invitation."""
    invitation = OrganisationInvitation.objects.select_for_update().select_related(
        "organisation"
    ).get(id=invitation.id)
    actor_membership = _manager_membership(actor=actor, organisation=invitation.organisation)
    _validate_assignable_role(actor_membership=actor_membership, role=invitation.role)
    if invitation.status != OrganisationInvitation.Status.PENDING:
        raise InvitationServiceError("Only a pending invitation can be resent.")

    raw_token = generate_token()
    invitation.token_digest = digest_token(raw_token)
    invitation.expires_at = _expiry_time()
    invitation.invited_by = actor
    invitation.save(
        update_fields=["token_digest", "expires_at", "invited_by", "updated_at"]
    )
    record_event(
        action="invitation.resent",
        object_type="organisation_invitation",
        object_id=str(invitation.id),
        actor=actor,
        organisation=invitation.organisation,
        metadata={
            "email": invitation.email,
            "role": invitation.role,
            "expires_at": invitation.expires_at,
        },
    )
    return invitation, raw_token


@transaction.atomic
def revoke_invitation(
    *,
    actor: User,
    invitation: OrganisationInvitation,
) -> OrganisationInvitation:
    """Revoke a pending invitation immediately."""
    invitation = OrganisationInvitation.objects.select_for_update().select_related(
        "organisation"
    ).get(id=invitation.id)
    actor_membership = _manager_membership(actor=actor, organisation=invitation.organisation)
    _validate_assignable_role(actor_membership=actor_membership, role=invitation.role)
    if invitation.status != OrganisationInvitation.Status.PENDING:
        raise InvitationServiceError("Only a pending invitation can be revoked.")

    invitation.status = OrganisationInvitation.Status.REVOKED
    invitation.revoked_at = timezone.now()
    invitation.save(update_fields=["status", "revoked_at", "updated_at"])
    record_event(
        action="invitation.revoked",
        object_type="organisation_invitation",
        object_id=str(invitation.id),
        actor=actor,
        organisation=invitation.organisation,
        metadata={"email": invitation.email, "role": invitation.role},
    )
    return invitation


def deliver_invitation(
    *,
    invitation: OrganisationInvitation,
    raw_token: str,
    actor: User,
) -> InvitationDelivery:
    """Send an invitation without making email availability a write dependency."""
    acceptance_url = build_acceptance_url(raw_token)
    subject = _("Invitation to join %(organisation)s on CrowdSmarter") % {
        "organisation": invitation.organisation.name
    }
    body = _(
        "You have been invited to join %(organisation)s as %(role)s.\n\n"
        "Accept the invitation and create or connect your account here:\n"
        "%(url)s\n\n"
        "This link expires at %(expires)s.\n"
        "If you were not expecting this invitation, you can ignore this email."
    ) % {
        "organisation": invitation.organisation.name,
        "role": invitation.get_role_display(),
        "url": acceptance_url,
        "expires": invitation.expires_at.isoformat(),
    }
    try:
        delivered = send_mail(
            subject=subject,
            message=body,
            from_email=notification_sender_email(),
            recipient_list=[invitation.email],
            fail_silently=False,
        )
    except Exception as exc:  # Email provider failures must not erase the invitation.
        logger.exception("Invitation delivery failed for invitation %s", invitation.id)
        record_event(
            action="invitation.delivery_failed",
            object_type="organisation_invitation",
            object_id=str(invitation.id),
            actor=actor,
            organisation=invitation.organisation,
            metadata={"error_type": type(exc).__name__},
        )
        return InvitationDelivery(
            status="failed",
            acceptance_url=acceptance_url if settings.DEBUG else None,
        )

    if delivered:
        now = timezone.now()
        OrganisationInvitation.objects.filter(id=invitation.id).update(
            last_sent_at=now,
            send_count=models.F("send_count") + 1,
            updated_at=now,
        )
        invitation.last_sent_at = now
        invitation.send_count += 1
        invitation.updated_at = now
        record_event(
            action="invitation.delivered",
            object_type="organisation_invitation",
            object_id=str(invitation.id),
            actor=actor,
            organisation=invitation.organisation,
            metadata={"email": invitation.email, "send_count": invitation.send_count},
        )
        status = "sent"
    else:
        record_event(
            action="invitation.delivery_failed",
            object_type="organisation_invitation",
            object_id=str(invitation.id),
            actor=actor,
            organisation=invitation.organisation,
            metadata={"error_type": "NoRecipientsDelivered"},
        )
        status = "failed"
    return InvitationDelivery(
        status=status,
        acceptance_url=acceptance_url if settings.DEBUG else None,
    )


@transaction.atomic
def accept_invitation(
    *,
    raw_token: str,
    authenticated_user: User | None,
    first_name: str = "",
    last_name: str = "",
    password: str = "",
) -> tuple[User, Membership, bool]:
    """Accept an invitation, creating an account only when one does not exist."""
    try:
        invitation = OrganisationInvitation.objects.select_for_update().select_related(
            "organisation"
        ).get(token_digest=digest_token(raw_token))
    except OrganisationInvitation.DoesNotExist as exc:
        raise InvitationServiceError("This invitation link is invalid.") from exc

    if invitation.status == OrganisationInvitation.Status.ACCEPTED:
        raise InvitationServiceError("This invitation has already been accepted.")
    if invitation.status == OrganisationInvitation.Status.REVOKED:
        raise InvitationServiceError("This invitation has been revoked.")
    if invitation.expires_at <= timezone.now():
        raise InvitationServiceError("This invitation has expired. Ask for a new invitation.")

    issuer_membership = Membership.objects.select_for_update().filter(
        organisation=invitation.organisation,
        user=invitation.invited_by,
        status=Membership.Status.ACTIVE,
    ).first()
    issuer_can_manage = issuer_membership is not None and issuer_membership.role in {
        Membership.Role.OWNER,
        Membership.Role.ADMIN,
    }
    issuer_can_assign_role = (
        invitation.role != Membership.Role.OWNER
        or (issuer_membership is not None and issuer_membership.role == Membership.Role.OWNER)
    )
    if not issuer_can_manage or not issuer_can_assign_role:
        raise InvitationServiceError(
            "This invitation is no longer authorised. Ask an organisation owner for a new one."
        )

    existing_user = User.objects.select_for_update().filter(
        email__iexact=invitation.email
    ).first()
    created_user = False

    if authenticated_user is not None:
        if authenticated_user.email.lower() != invitation.email:
            raise PermissionDenied(
                "Sign in with the email address that received this invitation."
            )
        user = authenticated_user
    elif existing_user is not None:
        raise InvitationServiceError(
            "An account already exists for this email. Sign in before accepting the invitation."
        )
    else:
        if not password:
            raise InvitationServiceError("Create a password to accept this invitation.")
        candidate = User(
            email=invitation.email,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
        )
        validate_password(password, user=candidate)
        user = User.objects.create_user(
            email=invitation.email,
            password=password,
            first_name=candidate.first_name,
            last_name=candidate.last_name,
        )
        created_user = True

    if Membership.objects.filter(
        organisation=invitation.organisation,
        user=user,
    ).exists():
        raise InvitationServiceError("This account is already a member of the organisation.")

    from apps.billing.services import assert_can_add_member

    assert_can_add_member(organisation=invitation.organisation)

    membership = Membership(
        organisation=invitation.organisation,
        user=user,
        role=invitation.role,
        status=Membership.Status.ACTIVE,
    )
    membership.full_clean(validate_unique=False, validate_constraints=False)
    try:
        membership.save()
    except IntegrityError as exc:
        raise InvitationServiceError("The membership could not be created safely.") from exc

    invitation.status = OrganisationInvitation.Status.ACCEPTED
    invitation.accepted_by = user
    invitation.accepted_at = timezone.now()
    invitation.save(
        update_fields=["status", "accepted_by", "accepted_at", "updated_at"]
    )
    if invitation.invited_by_id != user.id:
        create_notification(
            recipient=invitation.invited_by,
            organisation=invitation.organisation,
            kind=Notification.Kind.MEMBERSHIP,
            title="Invitation accepted",
            message=(
                f"{user.email} joined {invitation.organisation.name} as "
                f"{membership.get_role_display()}."
            ),
            url=f"/organisations/{invitation.organisation_id}",
            dedup_key=f"invitation-accepted:{invitation.id}",
        )
    record_event(
        action="invitation.accepted",
        object_type="organisation_invitation",
        object_id=str(invitation.id),
        actor=user,
        organisation=invitation.organisation,
        metadata={
            "email": invitation.email,
            "role": invitation.role,
            "created_account": created_user,
        },
    )
    MembershipEvent.objects.create(
        organisation=invitation.organisation,
        membership_id_snapshot=membership.id,
        user=user,
        actor=user,
        kind=MembershipEvent.Kind.CREATED,
        new_role=membership.role,
        new_status=membership.status,
        note="Membership created through invitation acceptance.",
    )
    record_event(
        action="membership.created",
        object_type="membership",
        object_id=str(membership.id),
        actor=user,
        organisation=invitation.organisation,
        metadata={
            "user_id": str(user.id),
            "role": membership.role,
            "source": "accepted_invitation",
            "invitation_id": str(invitation.id),
        },
    )
    return user, membership, created_user
