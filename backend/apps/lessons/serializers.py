"""API contracts for lessons learned."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.models import Decision
from apps.decisions.serializers import DecisionUserSerializer

from .models import Lesson


class LessonSerializer(serializers.ModelSerializer):
    created_by = DecisionUserSerializer(read_only=True)
    retired_by = DecisionUserSerializer(read_only=True)
    category_label = serializers.CharField(source="get_category_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Lesson
        fields = [
            "id",
            "decision_id",
            "title",
            "insight",
            "category",
            "category_label",
            "applicability",
            "recommended_change",
            "status",
            "status_label",
            "created_by",
            "retired_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LessonCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    insight = serializers.CharField(max_length=16000, trim_whitespace=True)
    category = serializers.ChoiceField(choices=Lesson.Category.choices)
    applicability = serializers.CharField(max_length=12000, trim_whitespace=True)
    recommended_change = serializers.CharField(
        max_length=12000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )


class LessonUpdateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    insight = serializers.CharField(max_length=16000, trim_whitespace=True, required=False)
    category = serializers.ChoiceField(choices=Lesson.Category.choices, required=False)
    applicability = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    recommended_change = serializers.CharField(
        max_length=12000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
    )

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class ArchiveDecisionSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    rationale = serializers.CharField(max_length=8000, trim_whitespace=True)
