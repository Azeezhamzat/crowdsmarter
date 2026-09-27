"""Small cross-cutting HTTP controls shared by every deployment."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from .observability import record_http_request

_SAFE_REQUEST_ID = re.compile(r"[A-Za-z0-9._-]{1,128}\Z")
logger = logging.getLogger("crowdsmarter.request")


class RequestIDMiddleware:
    """Attach a safe correlation identifier to every request and response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        supplied = request.headers.get("X-Request-ID", "")
        request_id = supplied if _SAFE_REQUEST_ID.fullmatch(supplied) else uuid.uuid4().hex
        request.request_id = request_id  # type: ignore[attr-defined]
        response = self.get_response(request)
        response["X-Request-ID"] = request_id
        return response


class HTTPObservabilityMiddleware:
    """Record bounded request metrics and one structured completion log."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        started = time.perf_counter()
        response = self.get_response(request)
        duration_seconds = time.perf_counter() - started
        match = getattr(request, "resolver_match", None)
        route = getattr(match, "view_name", None) or "unmatched"
        record_http_request(
            method=request.method or "UNKNOWN",
            route=route,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )
        log = logger.error if response.status_code >= 500 else logger.info
        user = getattr(request, "user", None)
        log(
            "request.completed",
            extra={
                "request_id": getattr(request, "request_id", ""),
                "method": request.method,
                "route": route,
                "status_code": response.status_code,
                "duration_ms": round(duration_seconds * 1000, 2),
                "user_id": str(user.id) if getattr(user, "is_authenticated", False) else "",
            },
        )
        return response
