"""Invitation permission matrix tests."""

from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.invitations.models import OrganisationInvitation
from apps.invitations.permissions import CanManageInvitations
from apps.invitations.tokens import digest_token
from apps.organisations.models import Membership


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("role", "expected"),
    [
        (Membership.Role.OWNER, True),
        (Membership.Role.ADMIN, True),
        (Membership.Role.CONTRIBUTOR, False),
        (Membership.Role.VIEWER, False),
    ],
)
def test_invitation_management_permission_by_role(
    role,
    expected,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    actor = owner if role == Membership.Role.OWNER else user_factory()
    organisation = organisation_factory(owner=owner)
    if actor != owner:
        Membership.objects.create(
            organisation=organisation,
            user=actor,
            role=role,
        )
    request = APIRequestFactory().post("/", {})
    force_authenticate(request, actor)
    request = Request(request)

    assert CanManageInvitations().has_object_permission(
        request,
        object(),
        organisation,
    ) is expected


@pytest.mark.django_db
def test_invitation_permission_uses_parent_organisation(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation = OrganisationInvitation.objects.create(
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
        token_digest=digest_token("permission-token"),
        invited_by=owner,
        expires_at=timezone.now() + timedelta(days=7),
    )
    request = APIRequestFactory().post("/", {})
    force_authenticate(request, owner)
    request = Request(request)

    assert CanManageInvitations().has_object_permission(
        request,
        object(),
        invitation,
    )
