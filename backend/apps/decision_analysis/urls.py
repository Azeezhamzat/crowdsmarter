from django.urls import path

from .views import (
    DecisionAnalysisWorkspaceView,
    DecisionIssueDetailView,
    DecisionIssueListCreateView,
    ExecutiveSummaryDetailView,
    ExecutiveSummaryListCreateView,
    QualityReviewDetailView,
    QualityReviewListCreateView,
)

app_name = "decision_analysis"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/analysis/",
        DecisionAnalysisWorkspaceView.as_view(),
        name="workspace",
    ),
    path(
        "decisions/<uuid:decision_id>/analysis/issues/",
        DecisionIssueListCreateView.as_view(),
        name="issues",
    ),
    path(
        "decision-analysis/issues/<uuid:issue_id>/",
        DecisionIssueDetailView.as_view(),
        name="issue-detail",
    ),
    path(
        "decisions/<uuid:decision_id>/analysis/quality-reviews/",
        QualityReviewListCreateView.as_view(),
        name="quality-reviews",
    ),
    path(
        "decision-analysis/quality-reviews/<uuid:review_id>/",
        QualityReviewDetailView.as_view(),
        name="quality-review-detail",
    ),
    path(
        "decisions/<uuid:decision_id>/analysis/executive-summaries/",
        ExecutiveSummaryListCreateView.as_view(),
        name="executive-summaries",
    ),
    path(
        "decision-analysis/executive-summaries/<uuid:summary_id>/",
        ExecutiveSummaryDetailView.as_view(),
        name="executive-summary-detail",
    ),
]
