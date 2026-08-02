from django.urls import path

from .views import (
    CommitmentCreateView,
    DecisionReviewDetailView,
    ImplementationStartView,
    OutcomeReviewCompleteView,
    OutcomeReviewOpenView,
)

app_name = "reviews"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/review/",
        DecisionReviewDetailView.as_view(),
        name="detail",
    ),
    path(
        "decisions/<uuid:decision_id>/commitment/",
        CommitmentCreateView.as_view(),
        name="commitment",
    ),
    path(
        "decisions/<uuid:decision_id>/implementation/start/",
        ImplementationStartView.as_view(),
        name="implementation-start",
    ),
    path(
        "decisions/<uuid:decision_id>/outcome-review/open/",
        OutcomeReviewOpenView.as_view(),
        name="outcome-review-open",
    ),
    path(
        "decisions/<uuid:decision_id>/outcome-review/complete/",
        OutcomeReviewCompleteView.as_view(),
        name="outcome-review-complete",
    ),
]
