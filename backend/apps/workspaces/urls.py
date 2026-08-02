"""Workspace API routes."""

from django.urls import path

from .views import WorkspaceDetailView, WorkspaceListCreateView

app_name = "workspaces"

urlpatterns = [
    path(
        "organisations/<uuid:organisation_id>/workspaces/",
        WorkspaceListCreateView.as_view(),
        name="list-create",
    ),
    path("workspaces/<uuid:workspace_id>/", WorkspaceDetailView.as_view(), name="detail"),
]
