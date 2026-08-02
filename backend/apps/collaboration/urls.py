from django.urls import path

from .views import (
    DecisionActivityView,
    DecisionDiscussionListCreateView,
    DiscussionEntryResolveView,
)

app_name = "collaboration"

urlpatterns = [
    path(
        "decisions/<uuid:decision_id>/discussion/",
        DecisionDiscussionListCreateView.as_view(),
        name="discussion-list-create",
    ),
    path(
        "discussion-entries/<uuid:entry_id>/resolve/",
        DiscussionEntryResolveView.as_view(),
        name="discussion-resolve",
    ),
    path(
        "decisions/<uuid:decision_id>/activity/",
        DecisionActivityView.as_view(),
        name="decision-activity",
    ),
]
