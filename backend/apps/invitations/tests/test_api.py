"""Invitation API, permission, CSRF, and regression tests."""

from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.invitations.services import create_invitation
from apps.organisations.models import Membership


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://localhost:5173",
    DEBUG=True,
)
def test_owner_can_create_list_resend_and_revoke_invitation(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    api_client.force_authenticate(owner)

    create_response = api_client.post(
        reverse("invitations:list-create", args=[organisation.id]),
        {"email": "person@example.com", "role": "contributor"},
        format="json",
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["invitation"]["email"] == "person@example.com"
    assert created["delivery"]["status"] == "sent"
    assert created["delivery"]["acceptance_url"].startswith("http://localhost:5173/")
    assert "#token=" in created["delivery"]["acceptance_url"]
    assert create_response["Cache-Control"] == "no-store"
    invitation_id = created["invitation"]["id"]

    list_response = api_client.get(reverse("invitations:list-create", args=[organisation.id]))
    assert list_response.status_code == 200
    assert [item["id"] for item in list_response.json()] == [invitation_id]

    resend_response = api_client.post(
        reverse("invitations:resend", args=[invitation_id]),
        {},
        format="json",
    )
    assert resend_response.status_code == 200
    assert resend_response.json()["invitation"]["send_count"] == 2

    revoke_response = api_client.post(
        reverse("invitations:revoke", args=[invitation_id]),
        {},
        format="json",
    )
    assert revoke_response.status_code == 200
    assert revoke_response.json()["status"] == "revoked"


@pytest.mark.django_db
def test_contributor_cannot_list_or_create_invitations(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    api_client.force_authenticate(contributor)
    url = reverse("invitations:list-create", args=[organisation.id])

    assert api_client.get(url).status_code == 403
    assert (
        api_client.post(
            url,
            {"email": "person@example.com", "role": "viewer"},
            format="json",
        ).status_code
        == 403
    )


@pytest.mark.django_db
def test_administrator_cannot_invite_owner_through_api(
    api_client,
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
    api_client.force_authenticate(administrator)

    response = api_client.post(
        reverse("invitations:list-create", args=[organisation.id]),
        {"email": "person@example.com", "role": "owner"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_public_invitation_get_and_new_account_acceptance_require_csrf(
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    _, raw_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="new.person@example.com",
        role=Membership.Role.CONTRIBUTOR,
    )
    url = reverse("invitations:accept")
    client = APIClient(enforce_csrf_checks=True)

    details_response = client.get(url, HTTP_X_INVITATION_TOKEN=raw_token)
    assert details_response.status_code == 200
    assert details_response.json()["account_exists"] is False
    assert details_response.json()["current_user_email"] is None
    assert details_response["Cache-Control"] == "no-store"

    no_csrf_response = APIClient(enforce_csrf_checks=True).post(
        url,
        {
            "first_name": "New",
            "last_name": "Person",
            "password": "A-strong-invited-password-123",
            "password_confirm": "A-strong-invited-password-123",
        },
        format="json",
        HTTP_X_INVITATION_TOKEN=raw_token,
    )
    assert no_csrf_response.status_code == 403

    csrf_token = details_response.cookies["csrftoken"].value
    accept_response = client.post(
        url,
        {
            "first_name": "New",
            "last_name": "Person",
            "password": "A-strong-invited-password-123",
            "password_confirm": "A-strong-invited-password-123",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_INVITATION_TOKEN=raw_token,
    )
    assert accept_response.status_code == 201
    payload = accept_response.json()
    assert payload["created_account"] is True
    assert payload["membership"]["organisation_id"] == str(organisation.id)
    assert client.get(reverse("accounts:me")).status_code == 200


@pytest.mark.django_db
def test_existing_account_signs_in_before_acceptance(
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
    url = reverse("invitations:accept")
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(url, HTTP_X_INVITATION_TOKEN=raw_token).cookies["csrftoken"].value

    anonymous_response = client.post(
        url,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_INVITATION_TOKEN=raw_token,
    )
    assert anonymous_response.status_code == 400
    assert "Sign in" in str(anonymous_response.json())

    client.force_authenticate(invited_user)
    authenticated_response = client.post(
        url,
        {},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_INVITATION_TOKEN=raw_token,
    )
    assert authenticated_response.status_code == 201
    assert authenticated_response.json()["created_account"] is False


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_BASE_URL="http://localhost:5173",
    DEBUG=True,
)
def test_resend_invalidates_old_secret(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    invitation, first_token = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("invitations:resend", args=[invitation.id]),
        {},
        format="json",
    )
    acceptance_url = response.json()["delivery"]["acceptance_url"]
    new_token = parse_qs(urlparse(acceptance_url).fragment)["token"][0]

    anonymous = APIClient()
    accept_url = reverse("invitations:accept")
    assert anonymous.get(accept_url, HTTP_X_INVITATION_TOKEN=first_token).status_code == 404
    assert anonymous.get(accept_url, HTTP_X_INVITATION_TOKEN=new_token).status_code == 200


@pytest.mark.django_db
def test_expired_invitation_is_reported_and_rejected(
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
    invitation.expires_at = timezone.now() - timedelta(minutes=1)
    invitation.save(update_fields=["expires_at", "updated_at"])
    client = APIClient(enforce_csrf_checks=True)
    url = reverse("invitations:accept")
    details = client.get(url, HTTP_X_INVITATION_TOKEN=raw_token)
    assert details.json()["status"] == "expired"
    csrf_token = details.cookies["csrftoken"].value

    response = client.post(
        url,
        {
            "password": "A-strong-invited-password-123",
            "password_confirm": "A-strong-invited-password-123",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_INVITATION_TOKEN=raw_token,
    )
    assert response.status_code == 400
    assert "expired" in str(response.json())


@pytest.mark.django_db
def test_non_manager_cannot_resend_or_revoke_invitation(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    contributor = user_factory()
    organisation = organisation_factory(owner=owner)
    Membership.objects.create(
        organisation=organisation,
        user=contributor,
        role=Membership.Role.CONTRIBUTOR,
    )
    invitation, _ = create_invitation(
        actor=owner,
        organisation=organisation,
        email="person@example.com",
        role=Membership.Role.VIEWER,
    )
    api_client.force_authenticate(contributor)

    assert (
        api_client.post(
            reverse("invitations:resend", args=[invitation.id]),
            {},
            format="json",
        ).status_code
        == 404
    )
    assert (
        api_client.post(
            reverse("invitations:revoke", args=[invitation.id]),
            {},
            format="json",
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_invitation_commands_reject_unexpected_fields(
    api_client,
    user_factory,
    organisation_factory,
):  # type: ignore[no-untyped-def]
    owner = user_factory()
    organisation = organisation_factory(owner=owner)
    api_client.force_authenticate(owner)

    response = api_client.post(
        reverse("invitations:list-create", args=[organisation.id]),
        {
            "email": "person@example.com",
            "role": "viewer",
            "status": "accepted",
        },
        format="json",
    )
    assert response.status_code == 400
    assert "status" in response.json()


@pytest.mark.django_db
def test_acceptance_endpoint_requires_secret_header():
    client = APIClient()
    assert client.get(reverse("invitations:accept")).status_code == 404
