"""Thin REST endpoints for Phase 15 integrated decision analysis."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .read_models import decision_analysis_workspace
from .selectors import (
    analysis_decision_for_user,
    issue_for_user,
    issues_for_decision,
    review_for_user,
    reviews_for_decision,
    summaries_for_decision,
    summary_for_user,
)
from .serializers import (
    DecisionIssuePatchSerializer,
    DecisionIssueSerializer,
    DecisionIssueWriteSerializer,
    ExecutiveSummaryPatchSerializer,
    ExecutiveSummarySerializer,
    ExecutiveSummaryWriteSerializer,
    QualityReviewPatchSerializer,
    QualityReviewSerializer,
    QualityReviewWriteSerializer,
)
from .services import (
    create_executive_summary,
    create_issue,
    create_quality_review,
    update_executive_summary,
    update_issue,
    update_quality_review,
)


class DecisionAnalysisWorkspaceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):
        decision = analysis_decision_for_user(user=request.user, decision_id=decision_id)
        return Response(decision_analysis_workspace(decision=decision, viewer=request.user))


class DecisionIssueListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):
        items = issues_for_decision(user=request.user, decision_id=decision_id)
        return Response(
            DecisionIssueSerializer(items, many=True, context={"request": request}).data
        )

    def post(self, request, decision_id):
        decision = analysis_decision_for_user(user=request.user, decision_id=decision_id)
        serializer = DecisionIssueWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_issue(actor=request.user, decision=decision, **serializer.validated_data)
        return Response(
            DecisionIssueSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class DecisionIssueDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, issue_id):
        item = issue_for_user(user=request.user, issue_id=issue_id)
        serializer = DecisionIssuePatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_issue(actor=request.user, issue=item, fields=dict(serializer.validated_data))
        return Response(DecisionIssueSerializer(item, context={"request": request}).data)


class QualityReviewListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):
        items = reviews_for_decision(user=request.user, decision_id=decision_id)
        return Response(
            QualityReviewSerializer(items, many=True, context={"request": request}).data
        )

    def post(self, request, decision_id):
        decision = analysis_decision_for_user(user=request.user, decision_id=decision_id)
        serializer = QualityReviewWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_quality_review(
            actor=request.user, decision=decision, **serializer.validated_data
        )
        return Response(
            QualityReviewSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class QualityReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, review_id):
        item = review_for_user(user=request.user, review_id=review_id)
        serializer = QualityReviewPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_quality_review(
            actor=request.user, review=item, fields=dict(serializer.validated_data)
        )
        return Response(QualityReviewSerializer(item, context={"request": request}).data)


class ExecutiveSummaryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, decision_id):
        items = summaries_for_decision(user=request.user, decision_id=decision_id)
        return Response(
            ExecutiveSummarySerializer(items, many=True, context={"request": request}).data
        )

    def post(self, request, decision_id):
        decision = analysis_decision_for_user(user=request.user, decision_id=decision_id)
        serializer = ExecutiveSummaryWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_executive_summary(
            actor=request.user, decision=decision, **serializer.validated_data
        )
        return Response(
            ExecutiveSummarySerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ExecutiveSummaryDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, summary_id):
        item = summary_for_user(user=request.user, summary_id=summary_id)
        serializer = ExecutiveSummaryPatchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = update_executive_summary(
            actor=request.user, summary=item, fields=dict(serializer.validated_data)
        )
        return Response(ExecutiveSummarySerializer(item, context={"request": request}).data)
