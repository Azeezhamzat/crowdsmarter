"""Participant API routes."""

from django.urls import path

from .views import ParticipantDetailView, ParticipantListCreateView

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
]
