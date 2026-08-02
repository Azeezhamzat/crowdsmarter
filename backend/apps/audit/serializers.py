"""Read-only API representation for audit events."""

from rest_framework import serializers

from apps.decisions.serializers import DecisionUserSerializer

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    actor = DecisionUserSerializer(read_only=True)

    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "action",
            "object_type",
            "object_id",
            "actor",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
