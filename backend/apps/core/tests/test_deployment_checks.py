from django.test import override_settings

from apps.core.checks import production_control_checks


def finding_ids():
    return {item.id for item in production_control_checks(None)}


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="",
    EMAIL_HOST_USER="",
    EMAIL_HOST_PASSWORD="",
    DEFAULT_FROM_EMAIL="invalid",
    SOURCE_ATTACHMENT_MALWARE_SCANNER="disabled",
    SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED=False,
    SOURCE_ATTACHMENT_ENFORCE_CLEAN_DOWNLOADS=False,
)
def test_deployment_checks_reject_missing_delivery_and_upload_controls():
    ids = finding_ids()
    assert {"crowdsmarter.E001", "crowdsmarter.E004", "crowdsmarter.E005"}.issubset(ids)
    assert {"crowdsmarter.E006", "crowdsmarter.E007"}.issubset(ids)


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="smtp.example.com",
    EMAIL_HOST_USER="hello@example.com",
    EMAIL_HOST_PASSWORD="secret",
    EMAIL_USE_TLS=True,
    EMAIL_USE_SSL=True,
    DEFAULT_FROM_EMAIL="CrowdSmarter <hello@example.com>",
    SOURCE_ATTACHMENT_MALWARE_SCANNER="clamav",
    SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED=True,
    SOURCE_ATTACHMENT_ENFORCE_CLEAN_DOWNLOADS=True,
)
def test_deployment_checks_reject_conflicting_smtp_encryption():
    assert "crowdsmarter.E002" in finding_ids()


@override_settings(
    DEBUG=False,
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="smtp.example.com",
    EMAIL_HOST_USER="hello@example.com",
    EMAIL_HOST_PASSWORD="secret",
    EMAIL_USE_TLS=True,
    EMAIL_USE_SSL=False,
    DEFAULT_FROM_EMAIL="CrowdSmarter <hello@example.com>",
    SOURCE_ATTACHMENT_MALWARE_SCANNER="clamav",
    SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED=True,
    SOURCE_ATTACHMENT_ENFORCE_CLEAN_DOWNLOADS=True,
    ENABLE_METRICS_ENDPOINT=True,
)
def test_provider_ready_settings_pass_crowdsmarter_checks():
    assert not [
        item for item in production_control_checks(None) if item.id.startswith("crowdsmarter")
    ]
