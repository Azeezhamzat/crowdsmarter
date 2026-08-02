"""Optional notification jobs. Core workflows do not depend on a worker."""

from celery import shared_task

from .services import deliver_due_review_notifications


@shared_task(ignore_result=True)
def send_due_review_notifications() -> int:
    return deliver_due_review_notifications()
