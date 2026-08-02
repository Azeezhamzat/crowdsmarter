"""Celery entry points for contribution reminders and digests."""

from celery import shared_task

from .services import deliver_due_reminders, deliver_email_digests


@shared_task(name="apps.contributions.tasks.send_contribution_reminders_and_digests")
def send_contribution_reminders_and_digests() -> dict[str, int]:
    return {
        "reminders": deliver_due_reminders(),
        "digests": deliver_email_digests(),
    }
