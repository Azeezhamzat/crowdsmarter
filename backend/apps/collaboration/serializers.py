"""API contracts for decision discussion and activity."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import DiscussionEntry
from .policies import can_resolve


class MentionedUserSerializer(DecisionUserSerializer):
    pass


class DiscussionEntrySerializer(serializers.ModelSerializer):
    author = DecisionUserSerializer(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    mentioned_users = MentionedUserSerializer(many=True, read_only=True)
    resolved_by = DecisionUserSerializer(read_only=True)
    is_resolved = serializers.BooleanField(read_only=True)
    can_resolve = serializers.SerializerMethodField()
    reply_to_summary = serializers.SerializerMethodField()

    class Meta:
        model = DiscussionEntry
        fields = [
            "id",
            "decision_id",
            "author",
            "kind",
            "kind_label",
            "body",
            "reply_to_id",
            "reply_to_summary",
            "mentioned_users",
            "is_resolved",
            "resolved_at",
            "resolved_by",
            "resolution_note",
            "can_resolve",
            "created_at",
        ]
        read_only_fields = fields

    def get_can_resolve(self, obj: DiscussionEntry) -> bool:
        request = self.context.get("request")
        return bool(request and can_resolve(actor=request.user, entry=obj))

    def get_reply_to_summary(self, obj: DiscussionEntry) -> dict | None:
        if not obj.reply_to:
            return None
        return {
            "id": str(obj.reply_to.id),
            "author_email": obj.reply_to.author.email,
            "kind": obj.reply_to.kind,
            "body_excerpt": obj.reply_to.body[:180],
        }


class DiscussionEntryCreateSerializer(StrictSerializer):
    kind = serializers.ChoiceField(choices=DiscussionEntry.Kind.choices)
    body = serializers.CharField(max_length=12000, trim_whitespace=True)
    mentioned_user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
    )
    reply_to_id = serializers.UUIDField(required=False, allow_null=True)


class DiscussionResolveSerializer(StrictSerializer):
    resolution_note = serializers.CharField(max_length=8000, trim_whitespace=True)


class DecisionActivityItemSerializer(serializers.Serializer):
    id = serializers.CharField()
    source = serializers.ChoiceField(  # type: ignore[assignment]  # API field shadows DRF Field.source.
        choices=["audit", "discussion"]
    )
    action = serializers.CharField()
    title = serializers.CharField()
    actor = DecisionUserSerializer(allow_null=True)
    created_at = serializers.DateTimeField()
    url = serializers.CharField(allow_blank=True)
    metadata = serializers.JSONField()
