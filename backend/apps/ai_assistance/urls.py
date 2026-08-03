"""AI assistance API routes."""

from django.urls import path

from .views import (
    AIReviewAcknowledgeView,
    AIReviewDetailView,
    AIReviewDismissView,
    DecisionAIReviewListCreateView,
    OrganisationAIReviewQualityView,
)

app_name = "ai_assistance"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/ai-reviews/",
        DecisionAIReviewListCreateView.as_view(),
        name="list-create",
    ),
    path("ai-reviews/<uuid:review_id>/", AIReviewDetailView.as_view(), name="detail"),
    path(
        "ai-reviews/<uuid:review_id>/acknowledge/",
        AIReviewAcknowledgeView.as_view(),
        name="acknowledge",
    ),
    path(
        "ai-reviews/<uuid:review_id>/dismiss/",
        AIReviewDismissView.as_view(),
        name="dismiss",
    ),
    path(
        "organisations/<uuid:organisation_id>/ai-assistance/quality/",
        OrganisationAIReviewQualityView.as_view(),
        name="organisation-quality",
    ),
]
