"""Session authentication and account self-service API views."""

from django.contrib.auth import (
    authenticate,
    get_user_model,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.tokens import default_token_generator
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CurrentUserSerializer,
    LoginSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileUpdateSerializer,
)
from .services import request_password_reset, set_new_password, update_profile
from .throttles import (
    AccountSecurityThrottle,
    LoginRateThrottle,
    PasswordResetConfirmThrottle,
    PasswordResetRequestThrottle,
)

User = get_user_model()


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
        normalised_email = serializer.validated_data["email"].strip().lower()
        user = authenticate(
            request=request,
            username=normalised_email,
            password=serializer.validated_data["password"],
        )
        if user is None or not user.is_active:
            return Response(
                {"detail": "Invalid email or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(CurrentUserSerializer(user).data)


class SessionLogoutView(APIView):
    """Destroy the current server-side session."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):  # type: ignore[no-untyped-def]
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class CurrentUserView(APIView):
    """Return or update the authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        return Response(CurrentUserSerializer(request.user).data)

    def patch(self, request):  # type: ignore[no-untyped-def]
        serializer = ProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = update_profile(user=request.user, **serializer.validated_data)
        return Response(CurrentUserSerializer(user).data)


class PasswordChangeView(APIView):
    """Allow an authenticated user to change their own password."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [AccountSecurityThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"user": request.user},
        )
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(serializer.validated_data["current_password"]):
            return Response(
                {"current_password": ["The current password is incorrect."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        set_new_password(
            user=request.user,
            new_password=serializer.validated_data["new_password"],
            actor=request.user,
        )
        update_session_auth_hash(request, request.user)
        return Response({"detail": "Password changed successfully."})


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetRequestView(APIView):
    """Accept an anonymous password-recovery request without account enumeration."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [PasswordResetRequestThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        dispatch = request_password_reset(email=serializer.validated_data["email"])
        payload: dict[str, object] = {
            "detail": (
                "If an active account exists for that email address, a password-reset "
                "link has been sent."
            )
        }
        if dispatch.development_url:
            payload["development_reset_url"] = dispatch.development_url
        response = Response(payload, status=status.HTTP_202_ACCEPTED)
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(csrf_protect, name="dispatch")
class PasswordResetConfirmView(APIView):
    """Validate a reset token and replace the account password."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [PasswordResetConfirmThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        raw_uid = request.data.get("uid", "")
        try:
            user_id = force_str(urlsafe_base64_decode(raw_uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        if user is None or not default_token_generator.check_token(
            user,
            serializer.validated_data["token"],
        ):
            return Response(
                {"detail": "This password-reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        set_new_password(
            user=user,
            new_password=serializer.validated_data["new_password"],
            actor=None,
        )
        response = Response({"detail": "Password reset successfully."})
        response["Cache-Control"] = "no-store"
        return response
