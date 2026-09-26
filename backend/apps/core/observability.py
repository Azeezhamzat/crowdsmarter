"""Dependency-free structured logging and process-local Prometheus metrics."""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

_LABEL_VALUE = re.compile(r"[^A-Za-z0-9_.:-]+")
_lock = threading.Lock()
_started_at = time.time()
_request_counts: defaultdict[tuple[str, str, str], int] = defaultdict(int)
_request_duration_sums: defaultdict[tuple[str, str], float] = defaultdict(float)
_request_duration_counts: defaultdict[tuple[str, str], int] = defaultdict(int)


def safe_label(value: str, *, fallback: str = "unknown") -> str:
    cleaned = _LABEL_VALUE.sub("_", value)[:120].strip("_")
    return cleaned or fallback


def record_http_request(
    *, method: str, route: str, status_code: int, duration_seconds: float
) -> None:
    method_label = safe_label(method.upper())
    route_label = safe_label(route)
    status_family = f"{status_code // 100}xx"
    with _lock:
        _request_counts[(method_label, route_label, status_family)] += 1
        _request_duration_sums[(method_label, route_label)] += duration_seconds
        _request_duration_counts[(method_label, route_label)] += 1


def prometheus_metrics() -> str:
    """Render a small, stable metric surface without high-cardinality URL labels."""
    lines = [
        "# HELP crowdsmarter_process_start_time_seconds Unix start time of this process.",
        "# TYPE crowdsmarter_process_start_time_seconds gauge",
        f"crowdsmarter_process_start_time_seconds {_started_at:.3f}",
        "# HELP crowdsmarter_http_requests_total HTTP requests handled by this process.",
        "# TYPE crowdsmarter_http_requests_total counter",
    ]
    with _lock:
        for (method, route, status_family), value in sorted(_request_counts.items()):
            lines.append(
                "crowdsmarter_http_requests_total"
                f'{{method="{method}",route="{route}",status_family="{status_family}"}} {value}'
            )
        lines.extend(
            [
                "# HELP crowdsmarter_http_request_duration_seconds Request duration by route.",
                "# TYPE crowdsmarter_http_request_duration_seconds summary",
            ]
        )
        for (method, route), duration_sum in sorted(_request_duration_sums.items()):
            labels = f'method="{method}",route="{route}"'
            lines.append(
                f"crowdsmarter_http_request_duration_seconds_sum{{{labels}}} {duration_sum:.6f}"
            )
            lines.append(
                "crowdsmarter_http_request_duration_seconds_count"
                f"{{{labels}}} {_request_duration_counts[(method, route)]}"
            )
    return "\n".join(lines) + "\n"


class JSONFormatter(logging.Formatter):
    """Emit one machine-readable JSON object per log record."""

    _extra_fields = (
        "request_id",
        "method",
        "route",
        "status_code",
        "duration_ms",
        "user_id",
        "task_name",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._extra_fields:
            value = getattr(record, field, None)
            if value not in (None, ""):
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))
