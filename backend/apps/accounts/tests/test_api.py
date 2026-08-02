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

    client.delete(
        reverse("accounts:logout"),
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    whitespace_login = client.post(
        reverse("accounts:login"),
        {"email": "  PERSON@example.com  ", "password": "correct-password"},
        format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert whitespace_login.status_code == 200

    me_response = client.get(reverse("accounts:me"))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "person@example.com"
    assert me_response.json()["is_staff"] is False

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
def test_inactive_account_uses_same_generic_login_error(
    user_factory,
):  # type: ignore[no-untyped-def]
    user_factory(
        email="inactive@example.com",
        password="correct-password",
        is_active=False,
    )
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    response = client.post(
        reverse("accounts:login"),
        {"email": "inactive@example.com", "password": "correct-password"},
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
def test_login_is_rate_limited(user_factory, monkeypatch):  # type: ignore[no-untyped-def]
    from apps.accounts.throttles import LoginRateThrottle

    monkeypatch.setattr(LoginRateThrottle, "rate", "1/min", raising=False)
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


@pytest.mark.django_db
def test_profile_update_is_self_service_and_audited(api_client, user_factory):  # type: ignore[no-untyped-def]
    from apps.audit.models import AuditEvent

    user = user_factory(first_name="Old", last_name="Name")
    api_client.force_authenticate(user)
    response = api_client.patch(
        reverse("accounts:me"),
        {"first_name": "  Amina ", "last_name": " Yusuf  "},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["first_name"] == "Amina"
    assert response.json()["last_name"] == "Yusuf"
    assert AuditEvent.objects.filter(
        action="account.profile_updated",
        object_id=str(user.id),
    ).exists()


@pytest.mark.django_db
def test_password_change_requires_current_password_and_preserves_session(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="Current-password-123")
    client = APIClient(enforce_csrf_checks=True)
    client.force_login(user)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    rejected = client.post(
        reverse("accounts:password-change"),
        {"current_password": "wrong", "new_password": "A-new-secure-password-456"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert rejected.status_code == 400

    changed = client.post(
        reverse("accounts:password-change"),
        {"current_password": "Current-password-123", "new_password": "A-new-secure-password-456"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert changed.status_code == 200
    assert client.get(reverse("accounts:me")).status_code == 200
    user.refresh_from_db()
    assert user.check_password("A-new-secure-password-456")


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", DEBUG=True)
def test_password_reset_is_generic_and_token_is_single_use(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="Current-password-123")
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    existing = client.post(
        reverse("accounts:password-reset-request"),
        {"email": "person@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    missing = client.post(
        reverse("accounts:password-reset-request"),
        {"email": "missing@example.com"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert existing.status_code == 202
    assert missing.status_code == 202
    assert existing.json()["detail"] == missing.json()["detail"]
    reset_url = existing.json()["development_reset_url"]
    fragment = reset_url.split("#", 1)[1]
    values = dict(part.split("=", 1) for part in fragment.split("&"))

    first = client.post(
        reverse("accounts:password-reset-confirm"),
        {
            "uid": values["uid"],
            "token": values["token"],
            "new_password": "A-new-secure-password-456",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert first.status_code == 200
    user.refresh_from_db()
    assert user.check_password("A-new-secure-password-456")

    second = client.post(
        reverse("accounts:password-reset-confirm"),
        {
            "uid": values["uid"],
            "token": values["token"],
            "new_password": "Another-secure-password-789",
        },
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert second.status_code == 400
    assert "invalid or has expired" in second.json()["detail"]
