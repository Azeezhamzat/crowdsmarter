"""API contracts for decision participants."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import Participant
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
