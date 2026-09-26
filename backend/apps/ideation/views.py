"""Public (unauthenticated) and org-authenticated open-session endpoints."""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.core.serializers import StrictSerializer
from apps.decisions.models import Decision
from apps.organisations.selectors import organisation_for_user
from apps.workspaces.selectors import workspace_for_user

from . import services
from .models import Idea, OpenSession
from .serializers import (
    IdeaArchiveSerializer,
    IdeaCommentCreateSerializer,
    IdeaCreateSerializer,
    OpenSessionCreateSerializer,
    OpenSessionOrganiserSerializer,
    OpenSessionPublicSerializer,
    OpenSessionSummarySerializer,
    SessionJoinSerializer,
)

PARTICIPANT_TOKEN_HEADER = "HTTP_X_PARTICIPANT_TOKEN"


class _SessionJoinThrottle(AnonRateThrottle):
    scope = "session_join"


class _IdeaSubmitThrottle(AnonRateThrottle):
    scope = "idea_submit"


class _IdeaVoteThrottle(AnonRateThrottle):
    scope = "idea_vote"


class _IdeaCommentThrottle(AnonRateThrottle):
    scope = "idea_comment"


def _participant_from_request(request, session: OpenSession):  # type: ignore[no-untyped-def]
    raw_token = request.META.get(PARTICIPANT_TOKEN_HEADER, "").strip()
    if not raw_token:
        raise PermissionDenied("Join this session before submitting or voting.")
    return services.participant_from_token(session=session, raw_token=raw_token)


def _public_session_response(session: OpenSession, *, participant=None) -> Response:
    ideas = services.ideas_for_session(session=session)
    voted = services.voted_idea_ids(session=session, participant=participant)
    data = OpenSessionPublicSerializer(
        session, context={"ideas": ideas, "voted_idea_ids": voted}
    ).data
    response = Response(data)
    response["Cache-Control"] = "no-store"
    return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
class OpenSessionPublicDetailView(APIView):
    """A session's public detail: prompt, description, and every idea with vote counts."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []

    def get(self, request, public_slug):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        participant = None
        raw_token = request.META.get(PARTICIPANT_TOKEN_HEADER, "").strip()
        if raw_token:
            try:
                participant = services.participant_from_token(session=session, raw_token=raw_token)
            except PermissionDenied:
                participant = None
        return _public_session_response(session, participant=participant)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SessionJoinView(APIView):
    """Register a lightweight name+email identity for one session."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_SessionJoinThrottle]

    def post(self, request, public_slug):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        serializer = SessionJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant, raw_token = services.identify_participant(
            session=session,
            existing_token=request.META.get(PARTICIPANT_TOKEN_HEADER, "").strip(),
            applicant_token=request.COOKIES.get(
                settings.APPLICANT_SESSION_COOKIE_NAME,
                "",
            ).strip(),
            **serializer.validated_data,
        )
        response = Response(
            {"participant_token": raw_token, "name": participant.name},
            status=status.HTTP_201_CREATED,
        )
        response["Cache-Control"] = "no-store"
        return response


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SessionIdeaCreateView(APIView):
    """Submit one idea to an open session."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_IdeaSubmitThrottle]

    def post(self, request, public_slug):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        participant = _participant_from_request(request, session)
        serializer = IdeaCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.submit_idea(session=session, participant=participant, **serializer.validated_data)
        return _public_session_response(session, participant=participant)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SessionIdeaVoteView(APIView):
    """Toggle one identity's vote on one idea."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_IdeaVoteThrottle]

    def post(self, request, public_slug, idea_id):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        participant = _participant_from_request(request, session)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        services.cast_vote(idea=idea, participant=participant)
        return _public_session_response(session, participant=participant)

    def delete(self, request, public_slug, idea_id):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        participant = _participant_from_request(request, session)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        services.remove_vote(idea=idea, participant=participant)
        return _public_session_response(session, participant=participant)


@method_decorator(ensure_csrf_cookie, name="dispatch")
@method_decorator(csrf_protect, name="dispatch")
class SessionIdeaCommentCreateView(APIView):
    """Post one deliberation comment on an idea."""

    permission_classes = [AllowAny]
    authentication_classes: list[type] = []
    throttle_classes = [_IdeaCommentThrottle]

    def post(self, request, public_slug, idea_id):  # type: ignore[no-untyped-def]
        session = services.public_session_by_slug(public_slug=public_slug)
        participant = _participant_from_request(request, session)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        serializer = IdeaCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.post_comment(idea=idea, participant=participant, **serializer.validated_data)
        return _public_session_response(session, participant=participant)


class OrganisationSessionListCreateView(APIView):
    """Org-authenticated: list and create open sessions for one organisation."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        sessions = services.list_sessions(actor=request.user, organisation=organisation)
        return Response(OpenSessionSummarySerializer(sessions, many=True).data)

    def post(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        serializer = OpenSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = dict(serializer.validated_data)
        decision_id = values.pop("decision_id", None)
        decision = None
        if decision_id:
            decision = get_object_or_404(Decision, id=decision_id, organisation=organisation)
        default_workspace_id = values.pop("default_workspace_id", None)
        default_workspace = None
        if default_workspace_id:
            default_workspace = workspace_for_user(
                user=request.user, workspace_id=default_workspace_id
            )
        session = services.create_session(
            actor=request.user,
            organisation=organisation,
            decision=decision,
            default_workspace=default_workspace,
            **values,
        )
        return Response(OpenSessionSummarySerializer(session).data, status=status.HTTP_201_CREATED)


def _organiser_session_response(request, session: OpenSession) -> Response:
    ideas = services.ideas_for_session(session=session)
    voted = services.voted_idea_ids(session=session, user=request.user)
    data = OpenSessionOrganiserSerializer(
        session, context={"ideas": ideas, "voted_idea_ids": voted}
    ).data
    return Response(data)


class OpenSessionOrganiserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):  # type: ignore[no-untyped-def]
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        return _organiser_session_response(request, session)


class OpenSessionStateActionSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=["open", "close"])


class OpenSessionStateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):  # type: ignore[no-untyped-def]
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        serializer = OpenSessionStateActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if serializer.validated_data["action"] == "open":
            services.open_session(actor=request.user, session=session)
        else:
            services.close_session(actor=request.user, session=session)
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        return _organiser_session_response(request, session)


class IdeaShortlistSerializer(StrictSerializer):
    shortlisted = serializers.BooleanField()


class IdeaShortlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, idea_id):  # type: ignore[no-untyped-def]
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        serializer = IdeaShortlistSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.shortlist_idea(actor=request.user, idea=idea, **serializer.validated_data)
        return _organiser_session_response(request, session)


class IdeaArchiveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, idea_id):  # type: ignore[no-untyped-def]
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        serializer = IdeaArchiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.archive_idea(actor=request.user, idea=idea, **serializer.validated_data)
        return _organiser_session_response(request, session)


class IdeaPromoteSerializer(StrictSerializer):
    decision_id = serializers.UUIDField(required=False, allow_null=True)


class IdeaPromoteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id, idea_id):  # type: ignore[no-untyped-def]
        session = services.session_for_organiser(actor=request.user, session_id=session_id)
        idea = get_object_or_404(Idea, id=idea_id, session=session)
        serializer = IdeaPromoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision_id = serializer.validated_data.get("decision_id")
        decision = (
            get_object_or_404(Decision, id=decision_id, organisation=session.organisation)
            if decision_id
            else None
        )
        services.promote_idea_to_decision(actor=request.user, idea=idea, decision=decision)
        return _organiser_session_response(request, session)
