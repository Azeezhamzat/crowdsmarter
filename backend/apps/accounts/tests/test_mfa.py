import time

import pytest
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts import totp
from apps.accounts.models import MFABackupCode, TOTPDevice
from apps.accounts.services import (
    MFAServiceError,
    begin_mfa_enrollment,
    confirm_mfa_enrollment,
    disable_mfa,
    mfa_is_enabled,
    verify_mfa_code,
)


def _current_code(secret: str) -> str:
    return totp._hotp(secret, int(time.time() // totp.PERIOD_SECONDS))


def _authenticated_client(user_factory, **kwargs):  # type: ignore[no-untyped-def]
    user = user_factory(**kwargs)
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    response = client.post(
        reverse("accounts:login"),
        {"email": user.email, "password": kwargs.get("password", "correct-password")},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert response.status_code == 200
    return user, client


def test_totp_verify_accepts_current_code_and_rejects_wrong_code():
    secret = totp.generate_secret()
    code = _current_code(secret)
    assert totp.verify_totp(secret=secret, code=code) is True
    wrong = "000000" if code != "000000" else "111111"
    assert totp.verify_totp(secret=secret, code=wrong) is False


@pytest.mark.django_db
def test_full_mfa_enrollment_and_login_flow(user_factory):  # type: ignore[no-untyped-def]
    user, client = _authenticated_client(user_factory, email="person@example.com", password="correct-password")
    assert client.get(reverse("accounts:mfa-status")).json()["is_enabled"] is False

    begin = client.post(
        reverse("accounts:mfa-enroll-begin"), {}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert begin.status_code == 200
    secret = begin.json()["secret"]
    assert begin.json()["provisioning_uri"].startswith("otpauth://totp/")

    confirm = client.post(
        reverse("accounts:mfa-enroll-confirm"), {"code": _current_code(secret)}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert confirm.status_code == 200
    backup_codes = confirm.json()["backup_codes"]
    assert len(backup_codes) == 10
    assert all("-" in code for code in backup_codes)
    assert client.get(reverse("accounts:mfa-status")).json()["is_enabled"] is True
    assert mfa_is_enabled(user=user) is True

    client.delete(reverse("accounts:logout"), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)

    login = client.post(
        reverse("accounts:login"), {"email": user.email, "password": "correct-password"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert login.status_code == 200
    assert login.json() == {"mfa_required": True}
    assert client.get(reverse("accounts:me")).status_code == 403

    verify = client.post(
        reverse("accounts:mfa-verify"), {"code": _current_code(secret)}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert verify.status_code == 200
    assert verify.json()["id"] == str(user.id)
    assert client.get(reverse("accounts:me")).status_code == 200


@pytest.mark.django_db
def test_backup_code_can_complete_login_and_is_single_use(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="correct-password")
    enrollment = begin_mfa_enrollment(user=user)
    backup_codes = confirm_mfa_enrollment(user=user, code=_current_code(enrollment.secret))
    a_code = backup_codes[0]

    assert verify_mfa_code(user=user, code=a_code) is True
    assert verify_mfa_code(user=user, code=a_code) is False

    device = TOTPDevice.objects.get(user=user)
    assert MFABackupCode.objects.filter(device=device, used_at__isnull=False).count() == 1


@pytest.mark.django_db
def test_mfa_disable_requires_correct_password(user_factory):  # type: ignore[no-untyped-def]
    user, client = _authenticated_client(user_factory, email="person@example.com", password="correct-password")
    enrollment = begin_mfa_enrollment(user=user)
    confirm_mfa_enrollment(user=user, code=_current_code(enrollment.secret))

    wrong = client.post(
        reverse("accounts:mfa-disable"), {"password": "wrong-password"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert wrong.status_code == 400
    assert mfa_is_enabled(user=user) is True

    correct = client.post(
        reverse("accounts:mfa-disable"), {"password": "correct-password"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert correct.status_code == 200
    assert mfa_is_enabled(user=user) is False

    with pytest.raises(MFAServiceError):
        disable_mfa(user=user)


@pytest.mark.django_db
def test_enroll_confirm_rejects_wrong_code(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="correct-password")
    begin_mfa_enrollment(user=user)
    with pytest.raises(MFAServiceError):
        confirm_mfa_enrollment(user=user, code="000000")


@pytest.mark.django_db
def test_cannot_begin_enrollment_when_already_enabled(user_factory):  # type: ignore[no-untyped-def]
    user = user_factory(email="person@example.com", password="correct-password")
    enrollment = begin_mfa_enrollment(user=user)
    confirm_mfa_enrollment(user=user, code=_current_code(enrollment.secret))
    with pytest.raises(MFAServiceError):
        begin_mfa_enrollment(user=user)


@pytest.mark.django_db
def test_mfa_verify_expires_after_the_pending_window(user_factory):  # type: ignore[no-untyped-def]
    user, client = _authenticated_client(user_factory, email="person@example.com", password="correct-password")
    enrollment = begin_mfa_enrollment(user=user)
    confirm_mfa_enrollment(user=user, code=_current_code(enrollment.secret))
    client.delete(reverse("accounts:logout"), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    client.post(
        reverse("accounts:login"), {"email": user.email, "password": "correct-password"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )

    with override_settings(MFA_PENDING_SESSION_SECONDS=300):
        session = client.session
        session["mfa_pending_started_at"] = time.time() - 301
        session.save()
        expired = client.post(
            reverse("accounts:mfa-verify"), {"code": _current_code(enrollment.secret)}, format="json",
            HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
        )
    assert expired.status_code == 400
    assert "expired" in expired.json()["detail"].lower()


@pytest.mark.django_db
def test_mfa_verify_is_rate_limited(user_factory, monkeypatch):  # type: ignore[no-untyped-def]
    from apps.accounts.throttles import MFAVerifyThrottle

    monkeypatch.setattr(MFAVerifyThrottle, "rate", "1/min", raising=False)
    cache.clear()
    user, client = _authenticated_client(user_factory, email="person@example.com", password="correct-password")
    enrollment = begin_mfa_enrollment(user=user)
    confirm_mfa_enrollment(user=user, code=_current_code(enrollment.secret))
    client.delete(reverse("accounts:logout"), HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value)
    client.post(
        reverse("accounts:login"), {"email": user.email, "password": "correct-password"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )

    first = client.post(
        reverse("accounts:mfa-verify"), {"code": "000000"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    second = client.post(
        reverse("accounts:mfa-verify"), {"code": "000000"}, format="json",
        HTTP_X_CSRFTOKEN=client.cookies["csrftoken"].value,
    )
    assert first.status_code == 400
    assert second.status_code == 429
