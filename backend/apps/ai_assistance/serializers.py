"""Strict API contracts for advisory AI reviews."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import AIReview
from .permissions import can_moderate_ai_review


class AIReviewSerializer(serializers.ModelSerializer):
    requested_by = DecisionUserSerializer(read_only=True)
    reviewed_by = DecisionUserSerializer(read_only=True)
    dismissed_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    is_reviewed = serializers.BooleanField(read_only=True)
    is_dismissed = serializers.BooleanField(read_only=True)
    can_review = serializers.SerializerMethodField()
    can_dismiss = serializers.SerializerMethodField()

    class Meta:
        model = AIReview
        fields = [
            "id",
            "decision_id",
            "status",
            "status_label",
            "provider_key",
            "provider_label",
            "model_identifier",
            "prompt_version",
            "input_fingerprint",
            "output",
            "error_message",
            "requested_by",
            "started_at",
            "completed_at",
            "is_reviewed",
            "reviewed_by",
            "reviewed_at",
            "review_notes",
            "is_dismissed",
            "dismissed_by",
            "dismissed_at",
            "dismissal_reason",
            "can_review",
            "can_dismiss",
            "created_at",
        ]
        read_only_fields = fields

    def _can_moderate(self, obj: AIReview) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and obj.status == AIReview.Status.COMPLETED
            and not obj.is_reviewed
            and not obj.is_dismissed
            and can_moderate_ai_review(actor=request.user, review=obj)
        )

    def get_can_review(self, obj: AIReview) -> bool:
        return self._can_moderate(obj)

    def get_can_dismiss(self, obj: AIReview) -> bool:
        return self._can_moderate(obj)


class AIReviewRequestSerializer(StrictSerializer):
    """An intentionally empty command; provider selection is configuration."""


class AIReviewAcknowledgeSerializer(StrictSerializer):
    notes = serializers.CharField(
        max_length=8000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )


class AIReviewDismissSerializer(StrictSerializer):
    reason = serializers.CharField(max_length=8000, trim_whitespace=True)


class AIReviewQualityMetricsSerializer(serializers.Serializer):
    total_completed = serializers.IntegerField()
    reviewed_count = serializers.IntegerField()
    dismissed_count = serializers.IntegerField()
    pending_disposition_count = serializers.IntegerField()
    correction_rate = serializers.FloatField(allow_null=True)
