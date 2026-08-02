from django.urls import path

from .views import (
    FeedSubscriptionListCreateView,
    FeedSubscriptionSyncView,
    ForesightOverviewView,
    SignalDecisionLinkView,
    SignalDetailView,
    SignalListCreateView,
    SourceAttachmentDownloadView,
    SourceAttachmentUploadView,
    SourceDetailView,
    SourceListCreateView,
    WatchlistDetailView,
    WatchlistListCreateView,
    WatchlistSignalView,
)

app_name = "foresight"

urlpatterns = [
    path("organisations/<uuid:organisation_id>/foresight/feeds/", FeedSubscriptionListCreateView.as_view(), name="feeds"),
    path("foresight/feeds/<uuid:feed_id>/sync/", FeedSubscriptionSyncView.as_view(), name="feed-sync"),
    path("organisations/<uuid:organisation_id>/foresight/overview/", ForesightOverviewView.as_view(), name="overview"),
    path("organisations/<uuid:organisation_id>/foresight/sources/", SourceListCreateView.as_view(), name="sources"),
    path("foresight/sources/<uuid:source_id>/", SourceDetailView.as_view(), name="source-detail"),
    path("foresight/sources/<uuid:source_id>/attachments/", SourceAttachmentUploadView.as_view(), name="source-attachment-upload"),
    path("foresight/attachments/<uuid:attachment_id>/download/", SourceAttachmentDownloadView.as_view(), name="source-attachment-download"),
    path("organisations/<uuid:organisation_id>/foresight/signals/", SignalListCreateView.as_view(), name="signals"),
    path("foresight/signals/<uuid:signal_id>/", SignalDetailView.as_view(), name="signal-detail"),
    path("foresight/signals/<uuid:signal_id>/decisions/", SignalDecisionLinkView.as_view(), name="signal-decision-link"),
    path("organisations/<uuid:organisation_id>/foresight/watchlists/", WatchlistListCreateView.as_view(), name="watchlists"),
    path("foresight/watchlists/<uuid:watchlist_id>/", WatchlistDetailView.as_view(), name="watchlist-detail"),
    path("foresight/watchlists/<uuid:watchlist_id>/signals/", WatchlistSignalView.as_view(), name="watchlist-signal-add"),
    path("foresight/watchlists/<uuid:watchlist_id>/signals/<uuid:signal_id>/", WatchlistSignalView.as_view(), name="watchlist-signal-remove"),
]

# Phase 12: structured foresight canvases and systems mapping.
from .mapping_views import (
    CanvasDetailView,
    CanvasListCreateView,
    ConsequenceListCreateView,
    DriverDetailView,
    DriverListCreateView,
    DriverSignalView,
    FeedbackLoopListCreateView,
    HorizonItemListCreateView,
    ImplicationDetailView,
    ImplicationListCreateView,
    RelationshipListCreateView,
    StakeholderListCreateView,
)

urlpatterns += [
    path("organisations/<uuid:organisation_id>/foresight/canvases/", CanvasListCreateView.as_view(), name="canvases"),
    path("foresight/canvases/<uuid:canvas_id>/", CanvasDetailView.as_view(), name="canvas-detail"),
    path("foresight/canvases/<uuid:canvas_id>/drivers/", DriverListCreateView.as_view(), name="canvas-drivers"),
    path("foresight/drivers/<uuid:driver_id>/", DriverDetailView.as_view(), name="driver-detail"),
    path("foresight/drivers/<uuid:driver_id>/signals/", DriverSignalView.as_view(), name="driver-signals"),
    path("foresight/canvases/<uuid:canvas_id>/stakeholders/", StakeholderListCreateView.as_view(), name="canvas-stakeholders"),
    path("foresight/canvases/<uuid:canvas_id>/relationships/", RelationshipListCreateView.as_view(), name="canvas-relationships"),
    path("foresight/canvases/<uuid:canvas_id>/feedback-loops/", FeedbackLoopListCreateView.as_view(), name="canvas-feedback-loops"),
    path("foresight/canvases/<uuid:canvas_id>/consequences/", ConsequenceListCreateView.as_view(), name="canvas-consequences"),
    path("foresight/canvases/<uuid:canvas_id>/horizons/", HorizonItemListCreateView.as_view(), name="canvas-horizons"),
    path("foresight/canvases/<uuid:canvas_id>/implications/", ImplicationListCreateView.as_view(), name="canvas-implications"),
    path("foresight/implications/<uuid:implication_id>/", ImplicationDetailView.as_view(), name="implication-detail"),
]

# Phase 13: scenario construction, wind-tunnelling, and adaptive signposts.
from .scenario_views import (
    ScenarioDetailView,
    ScenarioDriverStateView,
    ScenarioImplicationLinkView,
    ScenarioListCreateView,
    ScenarioReviewView,
    ScenarioSetDetailView,
    ScenarioSetListCreateView,
    SignpostListCreateView,
    SignpostObservationCreateView,
    WindTunnelAssessmentView,
)

urlpatterns += [
    path(
        "foresight/canvases/<uuid:canvas_id>/scenario-sets/",
        ScenarioSetListCreateView.as_view(),
        name="canvas-scenario-sets",
    ),
    path(
        "foresight/scenario-sets/<uuid:scenario_set_id>/",
        ScenarioSetDetailView.as_view(),
        name="scenario-set-detail",
    ),
    path(
        "foresight/scenario-sets/<uuid:scenario_set_id>/scenarios/",
        ScenarioListCreateView.as_view(),
        name="scenario-set-scenarios",
    ),
    path(
        "foresight/scenarios/<uuid:scenario_id>/",
        ScenarioDetailView.as_view(),
        name="scenario-detail",
    ),
    path(
        "foresight/scenarios/<uuid:scenario_id>/driver-states/",
        ScenarioDriverStateView.as_view(),
        name="scenario-driver-states",
    ),
    path(
        "foresight/scenarios/<uuid:scenario_id>/reviews/",
        ScenarioReviewView.as_view(),
        name="scenario-reviews",
    ),
    path(
        "foresight/scenarios/<uuid:scenario_id>/wind-tunnel/",
        WindTunnelAssessmentView.as_view(),
        name="scenario-wind-tunnel",
    ),
    path(
        "foresight/scenarios/<uuid:scenario_id>/implications/",
        ScenarioImplicationLinkView.as_view(),
        name="scenario-implications",
    ),
    path(
        "foresight/scenario-sets/<uuid:scenario_set_id>/signposts/",
        SignpostListCreateView.as_view(),
        name="scenario-set-signposts",
    ),
    path(
        "foresight/signposts/<uuid:signpost_id>/observations/",
        SignpostObservationCreateView.as_view(),
        name="signpost-observations",
    ),
]
