"""Deployment checks for controls that environment variables can silently weaken."""

from __future__ import annotations

from email.utils import parseaddr

from django.conf import settings
from django.core.checks import Error, Tags, Warning, register


@register(Tags.security, deploy=True)
def production_control_checks(app_configs, **kwargs):  # type: ignore[no-untyped-def]
    findings: list[Error | Warning] = []
    smtp_backend = "django.core.mail.backends.smtp.EmailBackend"
    console_backend = "django.core.mail.backends.console.EmailBackend"
    if smtp_backend == settings.EMAIL_BACKEND:
        missing = [
            name
            for name in ("EMAIL_HOST", "EMAIL_HOST_USER", "EMAIL_HOST_PASSWORD")
            if not str(getattr(settings, name, "")).strip()
        ]
        if missing:
            findings.append(
                Error(
                    f"SMTP delivery is missing required settings: {', '.join(missing)}.",
                    id="crowdsmarter.E001",
                )
            )
        if settings.EMAIL_USE_TLS and getattr(settings, "EMAIL_USE_SSL", False):
            findings.append(
                Error(
                    "EMAIL_USE_TLS and EMAIL_USE_SSL cannot both be enabled.",
                    id="crowdsmarter.E002",
                )
            )
    elif not settings.DEBUG and console_backend == settings.EMAIL_BACKEND:
        findings.append(
            Error(
                "The console email backend cannot deliver production messages.",
                id="crowdsmarter.E003",
            )
        )

    sender = parseaddr(settings.DEFAULT_FROM_EMAIL)[1]
    if "@" not in sender:
        findings.append(
            Error("DEFAULT_FROM_EMAIL must contain a valid mailbox.", id="crowdsmarter.E004")
        )
    if not settings.DEBUG and settings.SOURCE_ATTACHMENT_MALWARE_SCANNER != "clamav":
        findings.append(
            Error(
                "Production uploads must use SOURCE_ATTACHMENT_MALWARE_SCANNER=clamav.",
                id="crowdsmarter.E005",
            )
        )
    if not settings.DEBUG and not settings.SOURCE_ATTACHMENT_MALWARE_FAIL_CLOSED:
        findings.append(
            Error("Production malware scanning must fail closed.", id="crowdsmarter.E006")
        )
    if not settings.DEBUG and not settings.SOURCE_ATTACHMENT_ENFORCE_CLEAN_DOWNLOADS:
        findings.append(
            Error("Production downloads must require a clean scan.", id="crowdsmarter.E007")
        )
    if not settings.DEBUG and not settings.ENABLE_METRICS_ENDPOINT:
        findings.append(
            Warning(
                "The internal metrics endpoint is disabled; external observability must replace it.",
                id="crowdsmarter.W001",
            )
        )
    return findings
