"""Thin contribution-orchestration endpoints."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decision_options.selectors import option_for_user
from apps.decisions.selectors import decision_for_user

from .policies import can_manage_contributions
from .selectors import (
    contribution_preference,
    participation_summary,
    personal_contribution_work,
    request_for_user,
    requests_for_decision,
    session_for_user,
    session_participant_for_user,
    sessions_for_decision,
)
from .serializers import (
    ContributionDraftSerializer,
    ContributionPreferenceSerializer,
    ContributionPreferenceUpdateSerializer,
    ContributionRequestActionSerializer,
    ContributionRequestCreateSerializer,
    ContributionRequestSerializer,
    ContributionRequestUpdateSerializer,
    ContributionReviewInputSerializer,
    ContributionReviewSerializer,
    FacilitationSessionCreateSerializer,
    FacilitationSessionSerializer,
    FacilitationSessionStatusSerializer,
    SessionAttendanceSerializer,
    SessionParticipantSerializer,
)
from .services import (
    cancel_request,
    create_request,
    create_session,
    open_request,
    review_submission,
    save_draft,
    start_request,
    start_review,
    submit_request,
    update_preference,
    update_request,
    update_session_status,
    update_session_attendance,
)


class DecisionContributionRequestListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        requests = requests_for_decision(user=request.user, decision_id=decision_id)
        return Response({
            "can_manage": can_manage_contributions(actor=request.user, decision=decision),
            "participation": participation_summary(user=request.user, decision_id=decision_id),
            "requests": ContributionRequestSerializer(
                requests, many=True, context={"request": request}
            ).data,
        })

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ContributionRequestCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data.copy()
        option_id = values.pop("option_id", None)
        session_id = values.pop("session_id", None)
        option = option_for_user(user=request.user, option_id=option_id) if option_id else None
        session = session_for_user(user=request.user, session_id=session_id) if session_id else None
        item = create_request(
            actor=request.user,
            decision=decision,
            option=option,
            session=session,
            **values,
        )
        return Response(
            ContributionRequestSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ContributionRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        return Response(ContributionRequestSerializer(item, context={"request": request}).data)

    def patch(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        serializer = ContributionRequestUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_request(
            actor=request.user, request=item, changes=serializer.validated_data
        )
        return Response(ContributionRequestSerializer(item, context={"request": request}).data)


class ContributionRequestActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        serializer = ContributionRequestActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        if action == "open":
            item = open_request(actor=request.user, request=item)
        elif action == "start":
            item = start_request(actor=request.user, request=item)
        elif action == "start_review":
            item = start_review(actor=request.user, request=item)
        else:
            reason = serializer.validated_data.get("reason", "").strip()
            if not reason:
                from rest_framework.exceptions import ValidationError

                raise ValidationError({"reason": "Record why the request is being cancelled."})
            item = cancel_request(actor=request.user, request=item, reason=reason)
        return Response(ContributionRequestSerializer(item, context={"request": request}).data)


class ContributionDraftView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        serializer = ContributionDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = save_draft(actor=request.user, request=item, **serializer.validated_data)
        return Response({"id": str(submission.id), "sequence": submission.sequence, "status": submission.status})


class ContributionSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        serializer = ContributionDraftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = submit_request(actor=request.user, request=item, **serializer.validated_data)
        return Response(
            {"id": str(submission.id), "sequence": submission.sequence, "status": submission.status},
            status=status.HTTP_201_CREATED,
        )


class ContributionReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, request_id):  # type: ignore[no-untyped-def]
        item = request_for_user(user=request.user, request_id=request_id)
        serializer = ContributionReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = review_submission(actor=request.user, request=item, **serializer.validated_data)
        return Response(ContributionReviewSerializer(review).data, status=status.HTTP_201_CREATED)


class DecisionFacilitationSessionListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        sessions = sessions_for_decision(user=request.user, decision_id=decision_id)
        return Response(FacilitationSessionSerializer(
            sessions, many=True, context={"request": request}
        ).data)

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = FacilitationSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = create_session(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            FacilitationSessionSerializer(session, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class FacilitationSessionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, session_id):  # type: ignore[no-untyped-def]
        session = session_for_user(user=request.user, session_id=session_id)
        serializer = FacilitationSessionStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = update_session_status(actor=request.user, session=session, **serializer.validated_data)
        return Response(FacilitationSessionSerializer(session, context={"request": request}).data)


class SessionParticipantAttendanceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, participant_id):  # type: ignore[no-untyped-def]
        participant = session_participant_for_user(user=request.user, participant_id=participant_id)
        serializer = SessionAttendanceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        participant = update_session_attendance(
            actor=request.user, participant=participant, **serializer.validated_data
        )
        return Response(SessionParticipantSerializer(participant).data)


class PersonalContributionWorkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        payload = personal_contribution_work(user=request.user)
        return Response({
            "summary": payload["summary"],
            "requests": ContributionRequestSerializer(
                payload["requests"], many=True, context={"request": request}
            ).data,
        })


class ContributionPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        item = contribution_preference(user=request.user, organisation_id=organisation_id)
        return Response(ContributionPreferenceSerializer(item).data)

    def patch(self, request, organisation_id):  # type: ignore[no-untyped-def]
        item = contribution_preference(user=request.user, organisation_id=organisation_id)
        serializer = ContributionPreferenceUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_preference(preference=item, **serializer.validated_data)
        return Response(ContributionPreferenceSerializer(item).data)
