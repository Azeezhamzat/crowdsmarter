"""Tenant-safe notification inbox selectors."""

from uuid import UUID

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404

from apps.accounts.models import User

from .models import Notification


def notifications_for_user(
    *, user: User, unread_only: bool = False
) -> QuerySet[Notification]:
    queryset = Notification.objects.filter(recipient=user).select_related(
        "organisation", "decision"
    )
    if unread_only:
        queryset = queryset.filter(read_at__isnull=True)
    return queryset


def notification_for_user(
    *, user: User, notification_id: UUID
) -> Notification:
    return get_object_or_404(
        Notification.objects.select_related("organisation", "decision").filter(
            recipient=user
        ),
        id=notification_id,
    )
