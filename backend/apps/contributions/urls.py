from django.urls import path

from .views import (
    ContributionDraftView,
    ContributionPreferenceView,
    ContributionRequestActionView,
    ContributionRequestDetailView,
    ContributionReviewView,
    ContributionSubmitView,
    DecisionContributionRequestListCreateView,
    DecisionFacilitationSessionListCreateView,
    FacilitationSessionStatusView,
    PersonalContributionWorkView,
    SessionParticipantAttendanceView,
)

app_name = "contributions"

urlpatterns = [
    path("decisions/<uuid:decision_id>/contribution-requests/", DecisionContributionRequestListCreateView.as_view(), name="request-list-create"),
    path("contribution-requests/<uuid:request_id>/", ContributionRequestDetailView.as_view(), name="request-detail"),
    path("contribution-requests/<uuid:request_id>/actions/", ContributionRequestActionView.as_view(), name="request-action"),
    path("contribution-requests/<uuid:request_id>/draft/", ContributionDraftView.as_view(), name="request-draft"),
    path("contribution-requests/<uuid:request_id>/submit/", ContributionSubmitView.as_view(), name="request-submit"),
    path("contribution-requests/<uuid:request_id>/review/", ContributionReviewView.as_view(), name="request-review"),
    path("decisions/<uuid:decision_id>/facilitation-sessions/", DecisionFacilitationSessionListCreateView.as_view(), name="session-list-create"),
    path("facilitation-sessions/<uuid:session_id>/status/", FacilitationSessionStatusView.as_view(), name="session-status"),
    path("facilitation-participants/<uuid:participant_id>/attendance/", SessionParticipantAttendanceView.as_view(), name="session-attendance"),
    path("contributions/my-work/", PersonalContributionWorkView.as_view(), name="my-work"),
    path("organisations/<uuid:organisation_id>/contribution-preferences/", ContributionPreferenceView.as_view(), name="preferences"),
]
