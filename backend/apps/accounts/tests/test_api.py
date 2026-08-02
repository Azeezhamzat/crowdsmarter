import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_session_login_me_and_logout(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="correct-password")
    client = APIClient(enforce_csrf_checks=True)

    csrf_response = client.get(reverse("accounts:csrf"))
    csrf_token = csrf_response.cookies["csrftoken"].value

    login_response = client.post(
        reverse("accounts:login"),
        {"email": "PERSON@example.com", "password": "correct-password"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert login_response.status_code == 200
    assert login_response.json()["id"] == str(user.id)

    me_response = client.get(reverse("accounts:me"))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "person@example.com"

    rotated_csrf_token = client.cookies["csrftoken"].value
    logout_response = client.delete(
        reverse("accounts:logout"),
        HTTP_X_CSRFTOKEN=rotated_csrf_token,
    )
    assert logout_response.status_code == 204
    assert client.get(reverse("accounts:me")).status_code == 403


@pytest.mark.django_db
def test_login_rejects_missing_csrf(user_factory):  # type: ignore[no-untyped-def]
    user_factory(email="person@example.com", password="correct-password")
    client = APIClient(enforce_csrf_checks=True)
    response = client.post(
        reverse("accounts:login"),
        {"email": "person@example.com", "password": "correct-password"},
        format="json",
    )
    assert response.status_code == 403


@pytest.mark.django_db
def test_login_uses_generic_invalid_credentials_message(
    user_factory,
):  # type: ignore[no-untyped-def]
    user_factory(email="person@example.com", password="correct-password")
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    response = client.post(
        reverse("accounts:login"),
        {"email": "person@example.com", "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email or password."}


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_RATES": {"login": "1/min", "anon": "100/min", "user": "100/min"},
})
def test_login_is_rate_limited(user_factory):  # type: ignore[no-untyped-def]
    cache.clear()
    user_factory(email="person@example.com", password="correct-password")
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    first = client.post(
        reverse("accounts:login"),
        {"email": "person@example.com", "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    second = client.post(
        reverse("accounts:login"),
        {"email": "person@example.com", "password": "wrong"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert first.status_code == 400
    assert second.status_code == 429
