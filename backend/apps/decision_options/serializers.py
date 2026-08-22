"""API contracts for decision options."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.reasoning_policies import (
    can_edit_reasoning,
    can_manage_option_eligibility,
    can_manage_option_outcome,
)
from apps.decisions.serializers import DecisionUserSerializer

from .models import DecisionOption


class DecisionOptionSerializer(serializers.ModelSerializer):
    proposed_by = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    reversibility_label = serializers.CharField(
        source="get_reversibility_display", read_only=True, allow_null=True
    )
    eligibility_status_label = serializers.CharField(
        source="get_eligibility_status_display", read_only=True
    )
    outcome_status_label = serializers.CharField(
        source="get_outcome_status_display", read_only=True
    )
    depends_on_ids = serializers.PrimaryKeyRelatedField(
        source="depends_on", many=True, read_only=True
    )
    mutually_exclusive_with_ids = serializers.PrimaryKeyRelatedField(
        source="mutually_exclusive_with", many=True, read_only=True
    )
    can_edit = serializers.SerializerMethodField()
    can_manage_eligibility = serializers.SerializerMethodField()
    can_manage_outcome = serializers.SerializerMethodField()

    class Meta:
        model = DecisionOption
        fields = [
            "id",
            "decision_id",
            "title",
            "description",
            "expected_benefits",
            "tradeoffs",
            "is_status_quo",
            "estimated_cost",
            "cost_notes",
            "resource_notes",
            "implementation_time_estimate",
            "reversibility",
            "reversibility_label",
            "is_experiment",
            "experiment_notes",
            "depends_on_ids",
            "mutually_exclusive_with_ids",
            "status",
            "status_label",
            "eligibility_status",
            "eligibility_status_label",
            "eligibility_note",
            "eligibility_decided_at",
            "outcome_status",
            "outcome_status_label",
            "awarded_amount",
            "outcome_note",
            "outcome_decided_at",
            "proposed_by",
            "created_by",
            "can_edit",
            "can_manage_eligibility",
            "can_manage_outcome",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj: DecisionOption) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_edit_reasoning(
                actor=request.user,
                decision=obj.decision,
                created_by_id=obj.created_by_id,
            )
        )

    def get_can_manage_eligibility(self, obj: DecisionOption) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and can_manage_option_eligibility(actor=request.user, decision=obj.decision)
        )

    def get_can_manage_outcome(self, obj: DecisionOption) -> bool:
        request = self.context.get("request")
        return bool(
            request and can_manage_option_outcome(actor=request.user, decision=obj.decision)
        )


class DecisionOptionCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    description = serializers.CharField(max_length=12000, trim_whitespace=True)
    expected_benefits = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    tradeoffs = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    is_status_quo = serializers.BooleanField(required=False, default=False)
    proposed_by_id = serializers.UUIDField(required=False)
    estimated_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0
    )
    cost_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    resource_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    implementation_time_estimate = serializers.CharField(
        max_length=120, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    reversibility = serializers.ChoiceField(
        choices=DecisionOption.Reversibility.choices, required=False, allow_blank=True, default=""
    )
    is_experiment = serializers.BooleanField(required=False, default=False)
    experiment_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    depends_on_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    mutually_exclusive_with_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )


class DecisionOptionUpdateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    description = serializers.CharField(max_length=12000, trim_whitespace=True, required=False)
    expected_benefits = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    tradeoffs = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    is_status_quo = serializers.BooleanField(required=False)
    estimated_cost = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0
    )
    cost_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    resource_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    implementation_time_estimate = serializers.CharField(
        max_length=120, trim_whitespace=True, allow_blank=True, required=False
    )
    reversibility = serializers.ChoiceField(
        choices=DecisionOption.Reversibility.choices, required=False, allow_blank=True
    )
    is_experiment = serializers.BooleanField(required=False)
    experiment_notes = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    depends_on_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    mutually_exclusive_with_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    status = serializers.ChoiceField(choices=DecisionOption.Status.choices, required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class DecisionOptionEligibilitySerializer(StrictSerializer):
    eligibility_status = serializers.ChoiceField(choices=DecisionOption.EligibilityStatus.choices)
    eligibility_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )


class DecisionOptionOutcomeSerializer(StrictSerializer):
    outcome_status = serializers.ChoiceField(choices=DecisionOption.OutcomeStatus.choices)
    awarded_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, min_value=0, default=None
    )
    outcome_note = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if attrs["outcome_status"] == DecisionOption.OutcomeStatus.FUNDED and attrs.get("awarded_amount") is None:
            raise serializers.ValidationError(
                {"awarded_amount": "A funded outcome requires an awarded amount."}
            )
        return attrs
