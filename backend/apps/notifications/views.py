"""Thin endpoints for the current user's notification inbox."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .selectors import notification_for_user, notifications_for_user
from .serializers import NotificationSerializer
from .services import mark_all_notifications_read, mark_notification_read


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):  # type: ignore[no-untyped-def]
        unread_only = request.query_params.get("unread", "").lower() in {
            "1",
            "true",
            "yes",
        }
        queryset = notifications_for_user(user=request.user, unread_only=unread_only)
        unread_count = Notification.objects.filter(
            recipient=request.user,
            read_at__isnull=True,
        ).count()
        return Response(
            {
                "unread_count": unread_count,
                "notifications": NotificationSerializer(queryset[:100], many=True).data,
            }
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):  # type: ignore[no-untyped-def]
        notification = notification_for_user(
            user=request.user,
            notification_id=notification_id,
        )
        notification = mark_notification_read(notification=notification)
        return Response(NotificationSerializer(notification).data)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):  # type: ignore[no-untyped-def]
        count = mark_all_notifications_read(recipient=request.user)
        return Response({"marked_read": count}, status=status.HTTP_200_OK)
