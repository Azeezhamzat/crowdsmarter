"""Demo-request capture and optional notification workflows."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.db import transaction

from apps.platform_admin.contact import notification_sender_email

from .models import DemoRequest

logger = logging.getLogger(__name__)


@transaction.atomic
def create_demo_request(
    *,
    full_name: str,
    work_email: str,
    organisation_name: str,
    job_title: str = "",
    organisation_size: str,
    primary_need: str,
    message: str = "",
    consent_to_contact: bool,
) -> DemoRequest:
    """Persist a public demo request before attempting best-effort notification."""

    request = DemoRequest(
        full_name=full_name,
        work_email=work_email,
        organisation_name=organisation_name,
        job_title=job_title,
        organisation_size=organisation_size,
        primary_need=primary_need,
        message=message,
        consent_to_contact=consent_to_contact,
    )
    request.full_clean()
    request.save()
    transaction.on_commit(lambda: _notify_demo_request(request))
    return request


def _notify_demo_request(request: DemoRequest) -> None:
    """Notify the configured inbox and optionally acknowledge the requester."""

    recipient = getattr(settings, "DEMO_REQUEST_RECIPIENT", "").strip()
    public_reply_to = getattr(settings, "EMAIL_REPLY_TO", "").strip()
    try:
        from apps.platform_admin.models import PlatformConfiguration

        configuration = PlatformConfiguration.load()
        recipient = configuration.demo_email or recipient
        public_reply_to = configuration.public_contact_email or public_reply_to
    except Exception:  # The capture path must remain available during migration or recovery.
        logger.debug("Platform contact configuration is not available; using environment defaults.")
    if not recipient:
        return
    try:
        EmailMessage(
            subject=f"CrowdSmarter demo request - {request.organisation_name}",
            body=(
                f"Reference: {request.id}\n"
                f"Name: {request.full_name}\n"
                f"Work email: {request.work_email}\n"
                f"Organisation: {request.organisation_name}\n"
                f"Role: {request.job_title or 'Not provided'}\n"
                f"Organisation size: {request.get_organisation_size_display()}\n"
                f"Primary need: {request.get_primary_need_display()}\n\n"
                f"Context:\n{request.message or 'Not provided'}\n"
            ),
            from_email=notification_sender_email(),
            to=[recipient],
            reply_to=[request.work_email],
        ).send(fail_silently=False)

        if getattr(settings, "DEMO_REQUEST_SEND_ACKNOWLEDGEMENT", False):
            reply_to = public_reply_to or recipient
            EmailMessage(
                subject="We received your CrowdSmarter demonstration request",
                body=(
                    f"Hello {request.full_name},\n\n"
                    "Thank you for sharing your decision context. "
                    "We will review it and reply from our official CrowdSmarter inbox.\n\n"
                    f"Reference: {request.id}\n"
                    f"Contact: {reply_to}\n\n"
                    "CrowdSmarter\n"
                    "Foresight-to-decision intelligence"
                ),
                from_email=notification_sender_email(),
                to=[request.work_email],
                reply_to=[reply_to],
            ).send(fail_silently=False)
    except Exception:  # noqa: BLE001 - notification failure must not lose the request
        logger.exception(
            "Demo request %s was saved but notification delivery failed.", request.id
        )
