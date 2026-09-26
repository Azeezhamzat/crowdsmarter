"""Public applicant-portal endpoints: passwordless sign-in, cross-round applications, progress reports."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from . import services
from .serializers import (
    MagicLinkConsumeSerializer,
    MagicLinkRequestSerializer,
    MyApplicationSerializer,
    ProgressReportCreateSerializer,
)

APPLICANT_SESSION_COOKIE = settings.APPLICANT_SESSION_COOKIE_NAME


class _MagicLinkRequestThrottle(AnonRateThrottle):
    scope = "applicant_magic_link"


class _MagicLinkConsumeThrottle(AnonRateThrottle):
    scope = "applicant_magic_link_consume"


class _ProgressReportThrottle(AnonRateThrottle):
    scope = "applicant_progress_report"


def _account_from_request(request):  # type: ignore[no-untyped-def]
    raw_token = request.COOKIES.get(APPLICANT_SESSION_COOKIE, "").strip()
    if not raw_token:
        raise PermissionDenied("Sign in to view your applications.")
    return services.applicant_account_from_portal_token(raw_token=raw_token)


def _set_applicant_cookie(response: Response, raw_token: str) -> None:
    from django.conf import settings

    response.set_cookie(
        APPLICANT_SESSION_COOKIE,
        raw_token,
        max_age=getattr(settings, "APPLICANT_SESSION_TTL_HOURS", 8) * 60 * 60,
        httponly=True,
        secure=getattr(settings, "SESSION_COOKIE_SECURE", False),
        samesite="Lax",
        path="/",
    )


def _clear_applicant_cookie(response: Response) -> None:
    response.delete_cookie(
        APPLICANT_SESSION_COOKIE,
        samesite="Lax",
        path="/",
    )


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class MagicLinkRequestView(APIView):
    """Request a passwordless sign-in link by email. Never reveals whether an account exists."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_MagicLinkRequestThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = MagicLinkRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account, raw_token = services.request_magic_link(**serializer.validated_data)
        services.deliver_magic_link(account=account, raw_token=raw_token)
        response = Response({"status": "sent"}, status=status.HTTP_202_ACCEPTED)
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class MagicLinkConsumeView(APIView):
    """Exchange a one-time magic-link token for a portal bearer token."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_MagicLinkConsumeThrottle]

    def post(self, request):  # type: ignore[no-untyped-def]
        serializer = MagicLinkConsumeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        account, raw_portal_token = services.consume_magic_link(
            raw_token=serializer.validated_data["token"]
        )
        response = Response(
            {
                "email": account.email,
                "name": account.name,
            }
        )
        _set_applicant_cookie(response, raw_portal_token)
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class ApplicantSessionLogoutView(APIView):
    """Revoke the current applicant session and clear its HttpOnly cookie."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def delete(self, request):  # type: ignore[no-untyped-def]
        raw_token = request.COOKIES.get(APPLICANT_SESSION_COOKIE, "").strip()
        if raw_token:
            try:
                account = services.applicant_account_from_portal_token(raw_token=raw_token)
            except PermissionDenied:
                account = None
            if account is not None:
                services.revoke_portal_session(account=account)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        _clear_applicant_cookie(response)
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
class MyApplicationsView(APIView):
    """List every application submitted under the signed-in applicant account, across sessions."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request):  # type: ignore[no-untyped-def]
        account = _account_from_request(request)
        ideas = list(services.applications_for_account(account=account))
        reports_by_idea: dict = {}
        for idea in ideas:
            reports_by_idea[idea.id] = list(services.progress_reports_for_idea(idea=idea))
        data = MyApplicationSerializer(
            ideas, many=True, context={"progress_reports_by_idea": reports_by_idea}
        ).data
        response = Response({"email": account.email, "name": account.name, "applications": data})
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class ProgressReportCreateView(APIView):
    """Submit a post-award progress update against a funded application."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_ProgressReportThrottle]

    def post(self, request, idea_id):  # type: ignore[no-untyped-def]
        from apps.ideation.models import Idea

        account = _account_from_request(request)
        idea = get_object_or_404(Idea, id=idea_id)
        serializer = ProgressReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.submit_progress_report(account=account, idea=idea, **serializer.validated_data)
        ideas = list(services.applications_for_account(account=account))
        reports_by_idea = {i.id: list(services.progress_reports_for_idea(idea=i)) for i in ideas}
        data = MyApplicationSerializer(
            ideas, many=True, context={"progress_reports_by_idea": reports_by_idea}
        ).data
        return Response(
            {"email": account.email, "name": account.name, "applications": data},
            status=status.HTTP_201_CREATED,
        )
