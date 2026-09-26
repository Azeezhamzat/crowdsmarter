"""Operational health endpoints."""

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.db.utils import OperationalError
from django.http import HttpResponse
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .observability import prometheus_metrics


class LivenessView(APIView):
    """Confirm that the application process is running."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response({"status": "ok"})


class ReadinessView(APIView):
    """Confirm that the application can reach its required database."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        components = {"database": "up", "cache": "up"}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            components["database"] = "down"
        try:
            cache.set("crowdsmarter:readiness", "ok", timeout=5)
            if cache.get("crowdsmarter:readiness") != "ok":
                components["cache"] = "down"
        except Exception:  # noqa: BLE001 - readiness must report infrastructure failure
            components["cache"] = "down"
        available = all(value == "up" for value in components.values())
        return Response(
            {"status": "ok" if available else "unavailable", **components},
            status=200 if available else 503,
        )


class MetricsView(APIView):
    """Expose process metrics to an internal Prometheus scraper."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        if not getattr(settings, "ENABLE_METRICS_ENDPOINT", settings.DEBUG):
            return HttpResponse(status=404)
        return HttpResponse(
            prometheus_metrics(),
            content_type="text/plain; version=0.0.4; charset=utf-8",
        )
