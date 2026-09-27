"""Thin endpoints for attributable AI assistance."""

from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.decisions.selectors import decision_for_user
from apps.organisations.models import Membership
from apps.organisations.selectors import organisation_for_user

from .permissions import can_request_ai_review
from .selectors import review_for_user, reviews_for_decision
from .serializers import (
    AIReviewAcknowledgeSerializer,
    AIReviewDismissSerializer,
    AIReviewQualityMetricsSerializer,
    AIReviewRequestSerializer,
    AIReviewSerializer,
)
from .services import (
    ai_review_quality_metrics,
    dismiss_ai_review,
    mark_ai_review_reviewed,
    request_ai_review,
)


class DecisionAIReviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "ai_review"

    def get_throttles(self):  # type: ignore[no-untyped-def]
        if self.request.method == "POST":
            return super().get_throttles()
        return []

    def get(self, request, decision_id):  # type: ignore[no-untyped-def]
        reviews = reviews_for_decision(user=request.user, decision_id=decision_id)
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        return Response(
            {
                "can_request": can_request_ai_review(
                    actor=request.user,
                    decision=decision,
                ),
                "reviews": AIReviewSerializer(
                    reviews,
                    many=True,
                    context={"request": request},
                ).data,
            }
        )

    def post(self, request, decision_id):  # type: ignore[no-untyped-def]
        serializer = AIReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = decision_for_user(user=request.user, decision_id=decision_id)
        review = request_ai_review(actor=request.user, decision=decision)
        return Response(
            AIReviewSerializer(review, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class AIReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, review_id):  # type: ignore[no-untyped-def]
        review = review_for_user(user=request.user, review_id=review_id)
        return Response(AIReviewSerializer(review, context={"request": request}).data)


class AIReviewAcknowledgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):  # type: ignore[no-untyped-def]
        review = review_for_user(user=request.user, review_id=review_id)
        serializer = AIReviewAcknowledgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = mark_ai_review_reviewed(
            actor=request.user,
            review=review,
            **serializer.validated_data,
        )
        return Response(AIReviewSerializer(review, context={"request": request}).data)


class OrganisationAIReviewQualityView(APIView):
    """Owner/admin evaluation-harness view of how humans dispose of AI output."""

    permission_classes = [IsAuthenticated]

    def get(self, request, organisation_id):  # type: ignore[no-untyped-def]
        organisation = organisation_for_user(user=request.user, organisation_id=organisation_id)
        membership = organisation.memberships.filter(
            user=request.user,
            status=Membership.Status.ACTIVE,
        ).first()
        if membership is None or membership.role not in {
            Membership.Role.OWNER,
            Membership.Role.ADMIN,
        }:
            raise PermissionDenied(
                "Only organisation owners and administrators can view AI review quality metrics."
            )
        metrics = ai_review_quality_metrics(organisation=organisation)
        return Response(AIReviewQualityMetricsSerializer(metrics).data)


class AIReviewDismissView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):  # type: ignore[no-untyped-def]
        review = review_for_user(user=request.user, review_id=review_id)
        serializer = AIReviewDismissSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = dismiss_ai_review(
            actor=request.user,
            review=review,
            **serializer.validated_data,
        )
        return Response(AIReviewSerializer(review, context={"request": request}).data)
