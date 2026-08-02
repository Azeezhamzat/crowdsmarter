"""API contracts for immutable stakeholder positions."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import Position


class PositionSerializer(serializers.ModelSerializer):
    participant_user = DecisionUserSerializer(source="participant.user", read_only=True)
    participant_role_label = serializers.CharField(
        source="get_participant_role_display",
        read_only=True,
    )
    preferred_option_title = serializers.CharField(
        source="preferred_option.title",
        read_only=True,
        allow_null=True,
    )
    recommendation_label = serializers.CharField(
        source="get_recommendation_display",
        read_only=True,
    )
    confidence_label = serializers.CharField(
        source="get_confidence_display",
        read_only=True,
    )

    class Meta:
        model = Position
        fields = [
            "id",
            "decision_id",
            "participant_id",
            "participant_user",
            "participant_role",
            "participant_role_label",
            "preferred_option_id",
            "preferred_option_title",
            "recommendation",
            "recommendation_label",
            "rationale",
            "conditions",
            "confidence",
            "confidence_label",
            "version",
            "created_at",
        ]
        read_only_fields = fields


class PositionSubmitSerializer(StrictSerializer):
    preferred_option_id = serializers.UUIDField(required=False, allow_null=True)
    recommendation = serializers.ChoiceField(choices=Position.Recommendation.choices)
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)
    conditions = serializers.CharField(
        max_length=8000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    confidence = serializers.ChoiceField(
        choices=Position.Confidence.choices,
        required=False,
        default=Position.Confidence.MEDIUM,
    )
