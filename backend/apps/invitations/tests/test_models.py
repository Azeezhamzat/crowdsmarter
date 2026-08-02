"""Invitation model invariants."""

from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.invitations.models import OrganisationInvitation
from apps.invitations.tokens import digest_token
from apps.organisations.models import Membership


@pytest.mark.django_db
def test_invitation_normalises_email_and_never_stores_raw_token(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    raw_token = "a-secret-that-must-not-be-stored"
    invitation = OrganisationInvitation(
        organisation=organisation,
        email="  Person@Example.COM ",
        role=Membership.Role.CONTRIBUTOR,
        token_digest=digest_token(raw_token),
        invited_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )

    invitation.full_clean()
    invitation.save()

    assert invitation.email == "person@example.com"
    assert invitation.token_digest != raw_token
    assert len(invitation.token_digest) == 64


@pytest.mark.django_db
def test_invitation_rejects_unknown_role(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation = OrganisationInvitation(
        organisation=organisation,
        email="person@example.com",
        role="absolute-power",
        token_digest=digest_token("token"),
        invited_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )

    with pytest.raises(ValidationError):
        invitation.full_clean()


@pytest.mark.django_db
def test_invitation_state_fields_must_match_status(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation = OrganisationInvitation(
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
        status=OrganisationInvitation.Status.ACCEPTED,
        token_digest=digest_token("state-token"),
        invited_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )

    with pytest.raises(ValidationError):
        invitation.full_clean()
