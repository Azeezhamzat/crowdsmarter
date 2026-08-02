"""Thin public endpoint for requesting a CrowdSmarter demonstration."""

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DemoRequestCreateSerializer
from .services import create_demo_request
from .throttles import DemoRequestThrottle


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class DemoRequestCreateView(APIView):
    """Accept a strictly validated, rate-limited public demo request."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [DemoRequestThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = DemoRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        values.pop("website", None)
        demo_request = create_demo_request(**values)
        response = Response(
            {
                "detail": (
                    "Thank you. Your request has been received and the CrowdSmarter "
                    "team will respond using the work email you provided."
                ),
                "reference": str(demo_request.id),
            },
            status=status.HTTP_202_ACCEPTED,
        )
        response["Cache-Control"] = "no-store"
        return response
