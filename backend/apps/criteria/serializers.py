from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.reasoning_policies import can_edit_reasoning
from apps.decisions.serializers import DecisionUserSerializer

from .models import Criterion


class CriterionSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    direction_label = serializers.CharField(source="get_direction_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Criterion
        fields = [
            "id",
            "decision_id",
            "title",
            "description",
            "measurement_note",
            "direction",
            "direction_label",
            "weight",
            "weight_rationale",
            "is_must_have",
            "threshold_note",
            "owner",
            "order",
            "status",
            "status_label",
            "created_by",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: Criterion) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_edit_reasoning(
                actor=request.user,
                decision=obj.decision,
                created_by_id=obj.created_by_id,
                accountable_user_id=obj.owner_id,
            )
        )


class CriterionCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    measurement_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    direction = serializers.ChoiceField(choices=Criterion.Direction.choices)
    weight = serializers.IntegerField(min_value=0, max_value=100)
    weight_rationale = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    is_must_have = serializers.BooleanField(required=False, default=False)
    threshold_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    owner_id = serializers.UUIDField(required=False)
    order = serializers.IntegerField(min_value=0, required=False)


class CriterionUpdateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    measurement_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    direction = serializers.ChoiceField(choices=Criterion.Direction.choices, required=False)
    weight = serializers.IntegerField(min_value=0, max_value=100, required=False)
    weight_rationale = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    is_must_have = serializers.BooleanField(required=False)
    threshold_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    owner_id = serializers.UUIDField(required=False)
    order = serializers.IntegerField(min_value=0, required=False)
    status = serializers.ChoiceField(choices=Criterion.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
