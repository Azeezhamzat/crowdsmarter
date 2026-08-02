"""Background-task dispatch helpers.

Synchronous business workflows must commit successfully even when Redis or a
Celery worker is temporarily unavailable. Optional follow-up work is queued
best-effort and failures are logged for observability.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from django.db import transaction

logger = logging.getLogger(__name__)


def enqueue_after_commit(task: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    """Queue a Celery task after commit without breaking the user transaction."""

    def dispatch() -> None:
        try:
            task.delay(*args, **kwargs)
        except Exception:  # noqa: BLE001 - infrastructure failure must degrade gracefully
            logger.exception("Optional background task could not be queued", extra={"task": task})

    transaction.on_commit(dispatch)
