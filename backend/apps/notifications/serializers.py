"""API representations for the notification centre."""

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    is_read = serializers.BooleanField(read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "organisation_id",
            "decision_id",
            "kind",
            "kind_label",
            "title",
            "message",
            "url",
            "metadata",
            "is_read",
            "read_at",
            "created_at",
        ]
        read_only_fields = fields
