from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.reasoning_policies import can_edit_reasoning
from apps.decisions.serializers import DecisionUserSerializer

from .models import Assumption


class AssumptionSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    confidence_label = serializers.CharField(source="get_confidence_display", read_only=True)
    verification_status_label = serializers.CharField(
        source="get_verification_status_display", read_only=True
    )
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = Assumption
        fields = [
            "id", "decision_id", "option_id", "statement", "rationale", "impact_if_false",
            "confidence", "confidence_label", "verification_status",
            "verification_status_label", "verification_notes", "owner", "review_date",
            "status", "status_label", "created_by", "can_edit", "created_at", "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: Assumption) -> bool:
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


class AssumptionCreateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    statement = serializers.CharField(max_length=12000, trim_whitespace=True)
    rationale = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    impact_if_false = serializers.CharField(max_length=8000, trim_whitespace=True)
    confidence = serializers.ChoiceField(choices=Assumption.Confidence.choices)
    verification_status = serializers.ChoiceField(
        choices=Assumption.VerificationStatus.choices,
        required=False,
        default=Assumption.VerificationStatus.UNVERIFIED,
    )
    verification_notes = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    owner_id = serializers.UUIDField(required=False)
    review_date = serializers.DateField(required=False, allow_null=True)


class AssumptionUpdateSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    statement = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    rationale = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    impact_if_false = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    confidence = serializers.ChoiceField(choices=Assumption.Confidence.choices, required=False)
    verification_status = serializers.ChoiceField(
        choices=Assumption.VerificationStatus.choices, required=False
    )
    verification_notes = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    owner_id = serializers.UUIDField(required=False)
    review_date = serializers.DateField(required=False, allow_null=True)
    status = serializers.ChoiceField(choices=Assumption.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
