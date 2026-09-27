"""Scheduled preview-only retention reporting."""

import logging

from celery import shared_task

from .retention import retention_report

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True, name="apps.organisations.tasks.report_due_retention_reviews")
def report_due_retention_reviews() -> int:
    due = [row for row in retention_report() if row["eligible_for_manual_review"]]
    if due:
        logger.warning(
            "retention.manual_review_required",
            extra={"task_name": "report_due_retention_reviews"},
        )
    return len(due)
