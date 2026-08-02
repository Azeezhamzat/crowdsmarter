"""Thin API endpoints for the post-decision learning workflow."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user

from .selectors import review_for_user
from .serializers import (
    CommitmentInputSerializer,
    DecisionReviewSerializer,
    ImplementationOwnerInputSerializer,
    ImplementationStartInputSerializer,
    OutcomeReviewCompleteInputSerializer,
    OutcomeReviewOpenInputSerializer,
)
from .services import (
    change_implementation_owner,
    complete_outcome_review,
    open_outcome_review,
    record_commitment,
    start_implementation,
)


class DecisionReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        review = review_for_user(user=request.user, decision_id=decision_id)
        return Response(
            {"review": DecisionReviewSerializer(review).data if review else None}
        )

    def patch(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ImplementationOwnerInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = change_implementation_owner(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(DecisionReviewSerializer(review).data)


class CommitmentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = CommitmentInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = record_commitment(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(
            DecisionReviewSerializer(review).data,
            status=status.HTTP_201_CREATED,
        )


class ImplementationStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ImplementationStartInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = start_implementation(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(DecisionReviewSerializer(review).data)


class OutcomeReviewOpenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = OutcomeReviewOpenInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = open_outcome_review(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(DecisionReviewSerializer(review).data)


class OutcomeReviewCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        serializer = OutcomeReviewCompleteInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = complete_outcome_review(
            actor=request.user,
            decision=decision,
            **serializer.validated_data,
        )
        return Response(DecisionReviewSerializer(review).data)
