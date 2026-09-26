"""Invitation business workflow tests."""

from datetime import timedelta

import pytest
from django.core.exceptions import PermissionDenied
from django.test import override_settings
from django.utils import timezone

from apps.audit.models import AuditEvent
from apps.invitations.models import OrganisationInvitation
from apps.invitations.services import (
    InvitationServiceError,
    accept_invitation,
    create_invitation,
    deliver_invitation,
    effective_status,
    revoke_invitation,
    rotate_invitation,
)
from apps.invitations.tokens import digest_token
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_owner_creates_invitation_with_hashed_secret_and_audit(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)

    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="Person@Example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    assert invitation.email == "person@example.com"
    assert invitation.token_digest == digest_token(raw_token)
    assert invitation.token_digest != raw_token
    assert AuditEvent.objects.filter(
        action="invitation.created",
        object_id=str(invitation.id),
        actor=owner,
    ).exists()


@pytest.mark.django_db
def test_administrator_cannot_invite_owner(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    administrator = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=administrator,
        role=Membership.Role.ADMIN,
    )

    with pytest.raises(PermissionDenied, match="Only an owner"):
        create_invitation(
            actor=administrator,
            organisation=organisation,
            email="person@example.com",
            role=Membership.Role.OWNER,
        )


@pytest.mark.django_db
def test_cannot_invite_existing_member(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    member = user_factory(email="person@example.com")
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=member,
        role=Membership.Role.CONTRIBUTOR,
    )

    with pytest.raises(InvitationServiceError, match="already a member"):
        create_invitation(
            actor=owner,
            organisation=organisation,
            email="PERSON@example.com",
            role=Membership.Role.VIEWER,
        )


@pytest.mark.django_db
def test_duplicate_pending_invitation_requires_resend(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    with pytest.raises(InvitationServiceError, match="pending invitation"):
        create_invitation(
            actor=owner,
            organisation=organisation,
            email="person@example.com",
            role=Membership.Role.VIEWER,
        )


@pytest.mark.django_db
def test_resend_rotates_token_and_extends_expiry(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, first_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )
    first_expiry = invitation.expires_at

    invitation, second_token = rotate_invitation(actor=owner, invitation=invitation)

    assert first_token != second_token
    assert invitation.token_digest == digest_token(second_token)
    assert invitation.expires_at >= first_expiry
    assert AuditEvent.objects.filter(
        action="invitation.resent",
        object_id=str(invitation.id),
    ).exists()


@pytest.mark.django_db
def test_new_user_acceptance_creates_account_membership_and_audits(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="new.person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    user, membership, created_user = accept_invitation(
        raw_token=raw_token,
        authenticated_user=None,
        first_name="New",
        last_name="Person",
        password="A-strong-invited-password-123",
    )

    invitation.refresh_from_db()
    assert created_user is True
    assert user.email == "new.person@example.com"
    assert user.check_password("A-strong-invited-password-123")
    assert membership.organisation == organisation
    assert membership.role == Membership.Role.CONTRIBUTOR
    assert invitation.status == OrganisationInvitation.Status.ACCEPTED
    assert invitation.accepted_by == user
    assert AuditEvent.objects.filter(
        action="invitation.accepted",
        object_id=str(invitation.id),
        actor=user,
    ).exists()
    assert AuditEvent.objects.filter(
        action="membership.created",
        object_id=str(membership.id),
        actor=user,
        metadata__source="accepted_invitation",
    ).exists()


@pytest.mark.django_db
def test_existing_account_must_authenticate_before_accepting(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    invited_user = user_factory(email="person@example.com")
    organisation = organisation_factory(owner=owner)
    _, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email=invited_user.email,
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(InvitationServiceError, match="Sign in"):
        accept_invitation(
            raw_token=raw_token,
            authenticated_user=None,
            password="A-different-password-123",
        )

    _, membership, created_user = accept_invitation(
        raw_token=raw_token,
        authenticated_user=invited_user,
    )
    assert created_user is False
    assert membership.user == invited_user


@pytest.mark.django_db
def test_wrong_authenticated_account_cannot_accept(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    wrong_user = user_factory(email="wrong@example.com")
    organisation = organisation_factory(owner=owner)
    _, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )

    with pytest.raises(PermissionDenied, match="email address"):
        accept_invitation(
            raw_token=raw_token,
            authenticated_user=wrong_user,
        )


@pytest.mark.django_db
def test_expired_invitation_cannot_be_accepted(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )
    invitation.expires_at = timezone.now() - timedelta(seconds=1)
    invitation.save(update_fields=["expires_at", "updated_at"])

    assert effective_status(invitation) == "expired"
    with pytest.raises(InvitationServiceError, match="expired"):
        accept_invitation(
            raw_token=raw_token,
            authenticated_user=None,
            password="A-strong-invited-password-123",
        )


@pytest.mark.django_db
def test_revoked_invitation_cannot_be_accepted(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )

    revoke_invitation(actor=owner, invitation=invitation)

    with pytest.raises(InvitationServiceError, match="revoked"):
        accept_invitation(
            raw_token=raw_token,
            authenticated_user=None,
            password="A-strong-invited-password-123",
        )


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://localhost:5173",
    DEBUG=True,
)
def test_delivery_sends_acceptance_link_without_persisting_token(
    mailoutbox,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    result = deliver_invitation(
        invitation=invitation,
        raw_token=raw_token,
        actor=owner,
    )

    invitation.refresh_from_db()
    assert result.status == "sent"
    assert result.acceptance_url is not None
    assert raw_token in mailoutbox[0].body
    assert invitation.send_count == 1
    assert raw_token not in invitation.token_digest


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("locale", "subject_text", "body_text"),
    [
        ("fr", "Invitation à rejoindre", "Acceptez l'invitation"),
        ("ar", "دعوة للانضمام", "اقبل الدعوة"),
    ],
)
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://localhost:5173",
    DEBUG=True,
)
def test_delivery_translates_subject_and_body_under_active_locale(
    mailoutbox,
    user_factory,
    organisation_factory,
    locale,
    subject_text,
    body_text,
):  # type: ignore[no-untyped-def]
    from django.utils import translation

    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    with translation.override(locale):
        deliver_invitation(invitation=invitation, raw_token=raw_token, actor=owner)

    assert subject_text in mailoutbox[0].subject
    assert body_text in mailoutbox[0].body


@pytest.mark.django_db
def test_invitation_loses_authority_when_issuer_is_no_longer_a_manager(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    administrator = user_factory()
    organisation = organisation_factory(owner=owner)
    administrator_membership = Membership.objects.create(
        organisation=organisation,
        user=administrator,
        role=Membership.Role.ADMIN,
    )
    _, raw_token = create_invitation(
        actor=administrator,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )
    administrator_membership.role = Membership.Role.CONTRIBUTOR
    administrator_membership.save(update_fields=["role", "updated_at"])

    with pytest.raises(InvitationServiceError, match="no longer authorised"):
        accept_invitation(
            raw_token=raw_token,
            authenticated_user=None,
            password="A-strong-invited-password-123",
        )


@pytest.mark.django_db
def test_administrator_cannot_resend_or_revoke_owner_invitation(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    administrator = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=administrator,
        role=Membership.Role.ADMIN,
    )
    invitation, _ = create_invitation(
        actor=owner,
        organisation=organisation,
        email="future.owner@example.com",
        role=Membership.Role.OWNER,
    )

    with pytest.raises(PermissionDenied, match="Only an owner"):
        rotate_invitation(actor=administrator, invitation=invitation)
    with pytest.raises(PermissionDenied, match="Only an owner"):
        revoke_invitation(actor=administrator, invitation=invitation)


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_email_failure_does_not_remove_pending_invitation(
    monkeypatch,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )

    def fail_delivery(**kwargs):  # type: ignore[no-untyped-def]
        raise OSError("smtp unavailable")

    monkeypatch.setattr("apps.invitations.services.send_mail", fail_delivery)
    result = deliver_invitation(
        invitation=invitation,
        raw_token=raw_token,
        actor=owner,
    )

    invitation.refresh_from_db()
    assert result.status == "failed"
    assert result.acceptance_url is not None
    assert invitation.status == OrganisationInvitation.Status.PENDING
    assert invitation.send_count == 0
    assert AuditEvent.objects.filter(
        action="invitation.delivery_failed",
        object_id=str(invitation.id),
    ).exists()


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_zero_delivery_result_is_audited_without_removing_invitation(
    monkeypatch,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )

    monkeypatch.setattr("apps.invitations.services.send_mail", lambda **kwargs: 0)
    result = deliver_invitation(
        invitation=invitation,
        raw_token=raw_token,
        actor=owner,
    )

    invitation.refresh_from_db()
    assert result.status == "failed"
    assert invitation.status == OrganisationInvitation.Status.PENDING
    assert invitation.send_count == 0
    assert AuditEvent.objects.filter(
        action="invitation.delivery_failed",
        object_id=str(invitation.id),
        metadata__error_type="NoRecipientsDelivered",
    ).exists()


@pytest.mark.django_db
@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="https://crowdsmarter.example",
)
def test_production_delivery_does_not_return_secret_link_to_manager(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )

    result = deliver_invitation(
        invitation=invitation,
        raw_token=raw_token,
        actor=owner,
    )

    assert result.status == "sent"
    assert result.acceptance_url is None
