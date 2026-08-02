"""Session authentication API views."""

from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer, UserSerializer
from .throttles import LoginRateThrottle


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CsrfCookieView(APIView):
    """Issue a CSRF cookie before the browser submits credentials."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response({"detail": "CSRF cookie set."})


@method_decorator(csrf_protect, name="dispatch")
class SessionLoginView(APIView):
    """Create a server-side authenticated session."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [LoginRateThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            email=serializer.validated_data["email"].lower(),
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(UserSerializer(user).data)


class SessionLogoutView(APIView):
    """Destroy the current server-side session."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):  # type: ignore[no-untyped-def]
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    """Return the authenticated user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response(UserSerializer(request.user).data)
