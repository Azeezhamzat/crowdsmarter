"""Public, no-invitation self-serve signup: start your own commons for free."""

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework.test import APIClient

from apps.organisations.models import Membership, Organisation

User = get_user_model()


def _csrf_client() -> APIClient:
    return APIClient(enforce_csrf_checks=True)


@pytest.mark.django_db
def test_signup_creates_account_organisation_and_logs_in():  # type: ignore[no-untyped-def]
    client = _csrf_client()
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    response = client.post(
        reverse("accounts:signup"),
        {
            "full_name": "Amara Diallo",
            "email": "Amara@Example.com",
            "password": "a-genuinely-long-passphrase",
            "organisation_name": "Riverside Climate Commons",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "amara@example.com"
    assert body["organisation"]["name"] == "Riverside Climate Commons"
    assert body["organisation"]["slug"] == "riverside-climate-commons"

    user = User.objects.get(email="amara@example.com")
    assert user.first_name == "Amara"
    assert user.last_name == "Diallo"
    organisation = Organisation.objects.get(slug="riverside-climate-commons")
    membership = Membership.objects.get(organisation=organisation, user=user)
    assert membership.role == Membership.Role.OWNER
    assert membership.status == Membership.Status.ACTIVE

    # The signup response also establishes a logged-in session.
    me_response = client.get(reverse("accounts:me"))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "amara@example.com"


@pytest.mark.django_db
def test_signup_rejects_duplicate_email(user_factory):  # type: ignore[no-untyped-def]
    user_factory(email="taken@example.com")
    client = _csrf_client()
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    response = client.post(
        reverse("accounts:signup"),
        {
            "full_name": "Someone Else",
            "email": "taken@example.com",
            "password": "a-genuinely-long-passphrase",
            "organisation_name": "A New Commons",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.django_db
def test_signup_rejects_weak_password():  # type: ignore[no-untyped-def]
    client = _csrf_client()
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    response = client.post(
        reverse("accounts:signup"),
        {
            "full_name": "Someone New",
            "email": "weak@example.com",
            "password": "12345678",
            "organisation_name": "A New Commons",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 400
    assert not User.objects.filter(email="weak@example.com").exists()


@pytest.mark.django_db
def test_signup_rejects_filled_honeypot():  # type: ignore[no-untyped-def]
    client = _csrf_client()
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    response = client.post(
        reverse("accounts:signup"),
        {
            "full_name": "A Bot",
            "email": "bot@example.com",
            "password": "a-genuinely-long-passphrase",
            "organisation_name": "Spam Commons",
            "website": "https://spam.example",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 400
    assert not User.objects.filter(email="bot@example.com").exists()


@pytest.mark.django_db
def test_signup_requires_csrf():  # type: ignore[no-untyped-def]
    client = _csrf_client()
    response = client.post(
        reverse("accounts:signup"),
        {
            "full_name": "No Token",
            "email": "notoken@example.com",
            "password": "a-genuinely-long-passphrase",
            "organisation_name": "No Token Commons",
        },
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_signup_generates_unique_slug_on_name_collision():  # type: ignore[no-untyped-def]
    cache.clear()
    client = _csrf_client()
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    payload = {
        "full_name": "First Person",
        "email": "first@example.com",
        "password": "a-genuinely-long-passphrase",
        "organisation_name": "Shared Name Commons",
    }
    first = client.post(reverse("accounts:signup"), payload, format="json", HTTP_X_CSRFTOKEN=csrf_token)
    assert first.status_code == 201
    assert first.json()["organisation"]["slug"] == "shared-name-commons"

    client2 = _csrf_client()
    csrf_token2 = client2.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    payload["email"] = "second@example.com"
    second = client2.post(reverse("accounts:signup"), payload, format="json", HTTP_X_CSRFTOKEN=csrf_token2)
    assert second.status_code == 201
    assert second.json()["organisation"]["slug"] == "shared-name-commons-2"
