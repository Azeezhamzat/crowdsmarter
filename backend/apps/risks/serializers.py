from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.reasoning_policies import can_edit_reasoning
from apps.decisions.serializers import DecisionUserSerializer

from .models import Risk


class RiskSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    response_strategy_label = serializers.CharField(
        source="get_response_strategy_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    score = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Risk
        fields = [
            "id", "decision_id", "option_id", "title", "description", "likelihood",
            "impact", "score", "response_strategy", "response_strategy_label",
            "mitigation_plan", "owner", "review_date", "status", "status_label",
            "created_by", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: Risk) -> bool:
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


class RiskCreateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    likelihood = serializers.IntegerField(min_value=1, max_value=5)
    impact = serializers.IntegerField(min_value=1, max_value=5)
    response_strategy = serializers.ChoiceField(choices=Risk.ResponseStrategy.choices)
    mitigation_plan = serializers.CharField(
        max_length=12000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    owner_id = serializers.UUIDField(required=False)
    review_date = serializers.DateField(required=False, allow_null=True)


class RiskUpdateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    likelihood = serializers.IntegerField(min_value=1, max_value=5, required=False)
    impact = serializers.IntegerField(min_value=1, max_value=5, required=False)
    response_strategy = serializers.ChoiceField(
        choices=Risk.ResponseStrategy.choices,
        required=False,
    )
    mitigation_plan = serializers.CharField(
        max_length=12000, trim_whitespace=True, allow_blank=True, required=False
    )
    owner_id = serializers.UUIDField(required=False)
    review_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Risk.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
