"""API contracts for decision creation, framing, and lifecycle history."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.core.serializers import StrictSerializer

from .models import Decision, DecisionFinalisation, DecisionTransition
from .policies import (
    can_edit_decision,
    can_finalise_decision,
    can_manage_participants,
    can_transition_decision,
)
from .reasoning import reasoning_summary
from .reasoning_policies import can_contribute_reasoning
from .services import available_transition


class DecisionUserSerializer(serializers.ModelSerializer):
    """Minimal human identity shown in decision records."""

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name"]
        read_only_fields = fields


class DecisionSummarySerializer(serializers.ModelSerializer):
    """Compact decision representation for workspace lists."""

    owner = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Decision
        fields = [
            "id",
            "workspace_id",
            "title",
            "decision_question",
            "status",
            "status_label",
            "urgency",
            "target_decision_date",
            "owner",
            "updated_at",
        ]
        read_only_fields = fields


class DecisionDetailSerializer(serializers.ModelSerializer):
    """Full framing record with server-derived capabilities."""

    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_transition = serializers.SerializerMethodField()
    can_manage_participants = serializers.SerializerMethodField()
    next_transition = serializers.SerializerMethodField()
    can_contribute_reasoning = serializers.SerializerMethodField()
    reasoning_summary = serializers.SerializerMethodField()
    can_submit_position = serializers.SerializerMethodField()
    can_finalise = serializers.SerializerMethodField()
    position_summary = serializers.SerializerMethodField()

    class Meta:
        model = Decision
        fields = [
            "id",
            "organisation_id",
            "workspace_id",
            "title",
            "decision_question",
            "purpose",
            "context",
            "scope",
            "contribution_guidance",
            "urgency",
            "target_decision_date",
            "contribution_deadline",
            "status",
            "status_label",
            "status_changed_at",
            "owner",
            "created_by",
            "can_edit",
            "can_transition",
            "can_manage_participants",
            "next_transition",
            "can_contribute_reasoning",
            "reasoning_summary",
            "can_submit_position",
            "can_finalise",
            "position_summary",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def _actor(self):  # type: ignore[no-untyped-def]
        request = self.context.get("request")
        return request.user if request else None

    def get_can_edit(self, obj: Decision) -> bool:
        actor = self._actor()
        return bool(actor and can_edit_decision(actor=actor, decision=obj))

    def get_can_transition(self, obj: Decision) -> bool:
        actor = self._actor()
        return bool(actor and can_transition_decision(actor=actor, decision=obj))

    def get_can_manage_participants(self, obj: Decision) -> bool:
        actor = self._actor()
        return bool(actor and can_manage_participants(actor=actor, decision=obj))

    def get_next_transition(self, obj: Decision) -> dict | None:
        return available_transition(obj)

    def get_can_contribute_reasoning(self, obj: Decision) -> bool:
        actor = self._actor()
        return bool(actor and can_contribute_reasoning(actor=actor, decision=obj))

    def get_reasoning_summary(self, obj: Decision) -> dict:
        return reasoning_summary(obj)

    def get_can_submit_position(self, obj: Decision) -> bool:
        from apps.positions.policies import can_submit_position

        actor = self._actor()
        return bool(actor and can_submit_position(actor=actor, decision=obj))

    def get_can_finalise(self, obj: Decision) -> bool:
        actor = self._actor()
        return bool(actor and can_finalise_decision(actor=actor, decision=obj))

    def get_position_summary(self, obj: Decision) -> dict:
        from apps.positions.summary import position_summary

        return position_summary(obj)


class DecisionCreateSerializer(StrictSerializer):
    """Input contract for a new draft."""

    title = serializers.CharField(max_length=240, trim_whitespace=True)
    decision_question = serializers.CharField(
        max_length=4000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
    )
    owner_id = serializers.UUIDField(required=False)


class DecisionUpdateSerializer(StrictSerializer):
    """Explicit mutable framing fields; lifecycle state is excluded."""

    title = serializers.CharField(max_length=240, trim_whitespace=True, required=False)
    decision_question = serializers.CharField(
        max_length=4000, trim_whitespace=True, allow_blank=True, required=False
    )
    purpose = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    context = serializers.CharField(
        max_length=12000, trim_whitespace=True, allow_blank=True, required=False
    )
    scope = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    contribution_guidance = serializers.CharField(
        max_length=8000, trim_whitespace=True, allow_blank=True, required=False
    )
    urgency = serializers.ChoiceField(choices=Decision.Urgency.choices, required=False)
    target_decision_date = serializers.DateField(required=False, allow_null=True)
    contribution_deadline = serializers.DateTimeField(required=False, allow_null=True)
    owner_id = serializers.UUIDField(required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class DecisionTransitionInputSerializer(StrictSerializer):
    """Human command for one optimistic lifecycle transition."""

    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    rationale = serializers.CharField(
        max_length=8000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    warnings_acknowledged = serializers.ListField(
        child=serializers.CharField(max_length=240),
        required=False,
        allow_empty=True,
    )


class DecisionTransitionSerializer(serializers.ModelSerializer):
    """Immutable lifecycle history representation."""

    actor = DecisionUserSerializer(read_only=True)
    from_status_label = serializers.SerializerMethodField()
    to_status_label = serializers.SerializerMethodField()

    class Meta:
        model = DecisionTransition
        fields = [
            "id",
            "sequence",
            "from_status",
            "from_status_label",
            "to_status",
            "to_status_label",
            "actor",
            "rationale",
            "warnings_acknowledged",
            "created_at",
        ]
        read_only_fields = fields

    def get_from_status_label(self, obj: DecisionTransition) -> str:
        return Decision.Status(obj.from_status).label

    def get_to_status_label(self, obj: DecisionTransition) -> str:
        return Decision.Status(obj.to_status).label


class DecisionFinalisationSerializer(serializers.ModelSerializer):
    """Immutable human final decision record."""

    selected_option_title = serializers.CharField(
        source="selected_option.title",
        read_only=True,
    )
    decided_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = DecisionFinalisation
        fields = [
            "id",
            "decision_id",
            "selected_option_id",
            "selected_option_title",
            "decided_by",
            "rationale",
            "conditions",
            "dissent_summary",
            "position_snapshot",
            "decided_at",
            "created_at",
        ]
        read_only_fields = fields


class DecisionFinalisationInputSerializer(StrictSerializer):
    """Human command to select an option and finalise a decision."""

    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    selected_option_id = serializers.UUIDField()
    rationale = serializers.CharField(max_length=12000, trim_whitespace=True)
    conditions = serializers.CharField(
        max_length=8000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    dissent_summary = serializers.CharField(
        max_length=12000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    positions_reviewed = serializers.BooleanField()
