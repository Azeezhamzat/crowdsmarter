"""Open session API routes: public (shareable link) and org-authenticated (organiser)."""

from django.urls import path

from .views import (
    IdeaArchiveView,
    IdeaPromoteView,
    IdeaShortlistView,
    OpenSessionOrganiserDetailView,
    OpenSessionPublicDetailView,
    OpenSessionStateView,
    OrganisationSessionListCreateView,
    SessionIdeaCommentCreateView,
    SessionIdeaCreateView,
    SessionIdeaVoteView,
    SessionJoinView,
)

app_name = "ideation"

urlpatterns = [
    # Public, reachable via the shareable link only.
    path("public/sessions/<str:public_slug>/", OpenSessionPublicDetailView.as_view(), name="public-detail"),
    path("public/sessions/<str:public_slug>/join/", SessionJoinView.as_view(), name="public-join"),
    path("public/sessions/<str:public_slug>/ideas/", SessionIdeaCreateView.as_view(), name="public-idea-create"),
    path(
        "public/sessions/<str:public_slug>/ideas/<uuid:idea_id>/vote/",
        SessionIdeaVoteView.as_view(),
        name="public-idea-vote",
    ),
    path(
        "public/sessions/<str:public_slug>/ideas/<uuid:idea_id>/comments/",
        SessionIdeaCommentCreateView.as_view(),
        name="public-idea-comment",
    ),
    # Org-authenticated organiser surface.
    path(
        "organisations/<uuid:organisation_id>/sessions/",
        OrganisationSessionListCreateView.as_view(),
        name="organisation-list-create",
    ),
    path("sessions/<uuid:session_id>/", OpenSessionOrganiserDetailView.as_view(), name="organiser-detail"),
    path("sessions/<uuid:session_id>/state/", OpenSessionStateView.as_view(), name="organiser-state"),
    path(
        "sessions/<uuid:session_id>/ideas/<uuid:idea_id>/shortlist/",
        IdeaShortlistView.as_view(),
        name="idea-shortlist",
    ),
    path(
        "sessions/<uuid:session_id>/ideas/<uuid:idea_id>/promote/",
        IdeaPromoteView.as_view(),
        name="idea-promote",
    ),
    path(
        "sessions/<uuid:session_id>/ideas/<uuid:idea_id>/archive/",
        IdeaArchiveView.as_view(),
        name="idea-archive",
    ),
]
