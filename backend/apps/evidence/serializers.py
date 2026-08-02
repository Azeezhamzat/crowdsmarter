"""API contracts for evidence records."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.reasoning_policies import can_edit_reasoning
from apps.decisions.serializers import DecisionUserSerializer

from .models import Evidence


class EvidenceSerializer(serializers.ModelSerializer):
    created_by = DecisionUserSerializer(read_only=True)
    source_type_label = serializers.CharField(source="get_source_type_display", read_only=True)
    stance_label = serializers.CharField(source="get_stance_display", read_only=True)
    strength_label = serializers.CharField(source="get_strength_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = [
            "id", "decision_id", "option_id", "title", "summary", "source_type",
            "source_type_label", "source_reference", "source_url", "stance",
            "stance_label", "strength", "strength_label", "status", "status_label",
            "created_by", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: Evidence) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_edit_reasoning(
                actor=request.user,
                decision=obj.decision,
                created_by_id=obj.created_by_id,
            )
        )


class EvidenceCreateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    summary = serializers.CharField(max_length=12000, trim_whitespace=True)
    source_type = serializers.ChoiceField(choices=Evidence.SourceType.choices)
    source_reference = serializers.CharField(
        max_length=500, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    source_url = serializers.URLField(
        max_length=1000, allow_blank=True, required=False, default=""
    )
    stance = serializers.ChoiceField(choices=Evidence.Stance.choices)
    strength = serializers.ChoiceField(
        choices=Evidence.Strength.choices, required=False, default=Evidence.Strength.MODERATE
    )

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs.get("source_reference") and not attrs.get("source_url"):
            raise serializers.ValidationError(
                {"source_reference": "Provide a source reference or a source URL."}
            )
        return attrs


class EvidenceUpdateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    summary = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    source_type = serializers.ChoiceField(choices=Evidence.SourceType.choices, required=False)
    source_reference = serializers.CharField(
        max_length=500, trim_whitespace=True, allow_blank=True, required=False
    )
    source_url = serializers.URLField(max_length=1000, allow_blank=True, required=False)
    stance = serializers.ChoiceField(choices=Evidence.Stance.choices, required=False)
    strength = serializers.ChoiceField(choices=Evidence.Strength.choices, required=False)
    status = serializers.ChoiceField(choices=Evidence.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
