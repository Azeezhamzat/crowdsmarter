"""API contracts for decision participants."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import ConflictOfInterest, Participant
from .services import ASSIGNABLE_ROLES


class ParticipantSerializer(serializers.ModelSerializer):
    """Read representation of one active decision participant."""

    user = DecisionUserSerializer(read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Participant
        fields = [
            "id",
            "decision_id",
            "user",
            "role",
            "role_label",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ParticipantCreateSerializer(StrictSerializer):
    """Input contract for adding an existing organisation member."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=sorted(ASSIGNABLE_ROLES))


class ParticipantUpdateSerializer(StrictSerializer):
    """Input contract for changing stakeholder responsibility."""

    role = serializers.ChoiceField(choices=sorted(ASSIGNABLE_ROLES))


class ConflictOfInterestSerializer(serializers.ModelSerializer):
    """Read representation of one active or withdrawn conflict declaration."""

    participant_id = serializers.UUIDField(read_only=True)
    reviewer_email = serializers.EmailField(source="participant.user.email", read_only=True)
    option_id = serializers.UUIDField(read_only=True, allow_null=True)
    option_title = serializers.CharField(source="option.title", read_only=True, allow_null=True)
    scope_label = serializers.CharField(source="get_scope_display", read_only=True)

    class Meta:
        model = ConflictOfInterest
        fields = [
            "id",
            "participant_id",
            "reviewer_email",
            "option_id",
            "option_title",
            "scope",
            "scope_label",
            "reason",
            "declared_at",
            "withdrawn_at",
        ]
        read_only_fields = fields


class ConflictOfInterestCreateSerializer(StrictSerializer):
    """Input contract for declaring a conflict of interest."""

    scope = serializers.ChoiceField(choices=ConflictOfInterest.Scope.choices)
    option_id = serializers.UUIDField(required=False, allow_null=True)
    reason = serializers.CharField(
        max_length=2000, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
