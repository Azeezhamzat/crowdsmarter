"""Operational health endpoints."""

from django.db import connection
from django.db.utils import OperationalError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            return Response({"status": "unavailable", "database": "down"}, status=503)
        return Response({"status": "ok", "database": "up"})
