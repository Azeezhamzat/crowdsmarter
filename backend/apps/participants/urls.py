"""Participant API routes."""

from django.urls import path

from .views import (
    ConflictWithdrawView,
    ParticipantConflictListCreateView,
    ParticipantDetailView,
    ParticipantListCreateView,
)

app_name = "participants"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/participants/",
        ParticipantListCreateView.as_view(),
        name="list-create",
    ),
    path(
        "participants/<uuid:participant_id>/",
        ParticipantDetailView.as_view(),
        name="detail",
    ),
    path(
        "participants/<uuid:participant_id>/conflicts/",
        ParticipantConflictListCreateView.as_view(),
        name="conflict-list-create",
    ),
    path(
        "conflicts/<uuid:conflict_id>/withdraw/",
        ConflictWithdrawView.as_view(),
        name="conflict-withdraw",
    ),
]
