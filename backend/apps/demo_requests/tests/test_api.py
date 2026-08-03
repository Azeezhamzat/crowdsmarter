"""Public demo-request endpoint behaviour."""

import pytest
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.demo_requests.models import DemoRequest


VALID_REQUEST = {
    "full_name": "Amina Yusuf",
    "work_email": "AMINA@EXAMPLE.COM",
    "organisation_name": "Northstar Strategy",
    "job_title": "Director of Strategy",
    "organisation_size": "51-200",
    "primary_need": "strategic_foresight",
    "message": "We need a traceable foresight-to-decision workflow.",
    "consent_to_contact": True,
    "website": "",
}


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEMO_REQUEST_RECIPIENT="demo-owner@example.com",
)
def test_public_demo_request_is_stored_and_optionally_notified(
    django_capture_on_commit_callbacks,
):  # type: ignore[no-untyped-def]
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("demo_requests:create"),
            VALID_REQUEST,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    assert response.status_code == 202
    assert response["Cache-Control"] == "no-store"
    record = DemoRequest.objects.get()
    assert record.work_email == "amina@example.com"
    assert record.status == DemoRequest.Status.NEW
    assert response.json()["reference"] == str(record.id)
    assert len(mail.outbox) == 1
    assert "Northstar Strategy" in mail.outbox[0].subject
    assert mail.outbox[0].reply_to == ["amina@example.com"]


@pytest.mark.django_db
def test_demo_request_requires_csrf_and_contact_consent():
    client = APIClient(enforce_csrf_checks=True)
    missing_csrf = client.post(reverse("demo_requests:create"), VALID_REQUEST, format="json")
    assert missing_csrf.status_code == 403

    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value
    rejected = client.post(
        reverse("demo_requests:create"),
        {**VALID_REQUEST, "consent_to_contact": False},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    assert rejected.status_code == 400
    assert DemoRequest.objects.count() == 0


@pytest.mark.django_db
def test_demo_request_rejects_honeypot_and_unknown_fields():
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    honeypot = client.post(
        reverse("demo_requests:create"),
        {**VALID_REQUEST, "website": "https://spam.example"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    unknown = client.post(
        reverse("demo_requests:create"),
        {**VALID_REQUEST, "internal_status": "qualified"},
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert honeypot.status_code == 400
    assert unknown.status_code == 400
    assert DemoRequest.objects.count() == 0


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEMO_REQUEST_RECIPIENT="demo-owner@example.com",
)
def test_notification_failure_does_not_lose_demo_request(
    django_capture_on_commit_callbacks, monkeypatch
):  # type: ignore[no-untyped-def]
    def fail_delivery(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise RuntimeError("mail unavailable")

    monkeypatch.setattr("apps.demo_requests.services.EmailMessage.send", fail_delivery)
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("demo_requests:create"),
            VALID_REQUEST,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    assert response.status_code == 202
    assert DemoRequest.objects.count() == 1


@pytest.mark.django_db
@override_settings(REST_FRAMEWORK={
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_THROTTLE_RATES": {
        "demo_request": "1/hour",
        "anon": "100/hour",
        "user": "100/hour",
    },
})
def test_demo_request_is_rate_limited(monkeypatch):  # type: ignore[no-untyped-def]
    from apps.demo_requests.throttles import DemoRequestThrottle

    monkeypatch.setattr(DemoRequestThrottle, "rate", "1/hour", raising=False)
    cache.clear()
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    first = client.post(
        reverse("demo_requests:create"),
        VALID_REQUEST,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )
    second = client.post(
        reverse("demo_requests:create"),
        VALID_REQUEST,
        format="json",
        HTTP_X_CSRFTOKEN=csrf_token,
    )

    assert first.status_code == 202
    assert second.status_code == 429
    assert DemoRequest.objects.count() == 1


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEMO_REQUEST_RECIPIENT="hello@crowdsmarter.com",
    EMAIL_REPLY_TO="hello@crowdsmarter.com",
    DEMO_REQUEST_SEND_ACKNOWLEDGEMENT=True,
)
def test_demo_request_can_send_a_configured_acknowledgement(
    django_capture_on_commit_callbacks,
):  # type: ignore[no-untyped-def]
    client = APIClient(enforce_csrf_checks=True)
    csrf_token = client.get(reverse("accounts:csrf")).cookies["csrftoken"].value

    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("demo_requests:create"),
            VALID_REQUEST,
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

    assert response.status_code == 202
    assert len(mail.outbox) == 2
    assert mail.outbox[0].to == ["hello@crowdsmarter.com"]
    assert mail.outbox[0].reply_to == ["amina@example.com"]
    assert mail.outbox[1].to == ["amina@example.com"]
    assert mail.outbox[1].reply_to == ["hello@crowdsmarter.com"]
