"""Notification API routes."""

from django.urls import path

from .views import NotificationListView, NotificationReadAllView, NotificationReadView

app_name = "notifications"

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="list"),
    path(
        "notifications/read-all/",
        NotificationReadAllView.as_view(),
        name="read-all",
    ),
    path(
        "notifications/<uuid:notification_id>/read/",
        NotificationReadView.as_view(),
        name="read",
    ),
]
