from unittest.mock import Mock, patch

from apps.core.tasks import enqueue_after_commit


def test_optional_task_is_dispatched_only_after_commit():
    task = Mock()
    with patch("apps.core.tasks.transaction.on_commit") as on_commit:
        enqueue_after_commit(task, "decision-id", mode="review")

    task.delay.assert_not_called()
    callback = on_commit.call_args.args[0]
    callback()
    task.delay.assert_called_once_with("decision-id", mode="review")


def test_queue_failure_is_logged_without_raising():
    task = Mock()
    task.delay.side_effect = ConnectionError("Redis unavailable")
    with (
        patch("apps.core.tasks.transaction.on_commit") as on_commit,
        patch("apps.core.tasks.logger.exception") as log_exception,
    ):
        enqueue_after_commit(task, "decision-id")

    callback = on_commit.call_args.args[0]
    callback()
    log_exception.assert_called_once()
