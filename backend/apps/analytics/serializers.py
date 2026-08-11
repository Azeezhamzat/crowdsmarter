"""Serializers for attributable analytics insights."""

from rest_framework import serializers

from apps.accounts.serializers import UserSerializer

from .models import AnalyticsInsight


class AnalyticsInsightSerializer(serializers.ModelSerializer):
    requested_by = UserSerializer(read_only=True)

    class Meta:
        model = AnalyticsInsight
        fields = [
            "id",
            "provider_key",
            "provider_label",
            "model_identifier",
            "headline",
            "observations",
            "requested_by",
            "created_at",
        ]
        read_only_fields = fields
