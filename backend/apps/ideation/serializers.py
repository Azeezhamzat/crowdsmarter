"""Read/write representations for open sessions, ideas, and votes."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import Idea, IdeaComment, OpenSession


class SessionParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()


class IdeaCommentSerializer(serializers.ModelSerializer):
    submitted_by_participant = SessionParticipantSerializer(source="participant", read_only=True)
    submitted_by_user = DecisionUserSerializer(source="user", read_only=True)

    class Meta:
        model = IdeaComment
        fields = ["id", "body", "submitted_by_participant", "submitted_by_user", "created_at"]
        read_only_fields = fields


class IdeaSerializer(serializers.ModelSerializer):
    submitted_by_participant = SessionParticipantSerializer(read_only=True)
    submitted_by_user = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    vote_count = serializers.IntegerField(read_only=True)
    voted_by_me = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()
    comments = IdeaCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Idea
        fields = [
            "id",
            "title",
            "description",
            "category",
            "requested_amount",
            "status",
            "status_label",
            "submitted_by_participant",
            "submitted_by_user",
            "vote_count",
            "voted_by_me",
            "application_status",
            "comments",
            "created_at",
        ]
        read_only_fields = fields

    def get_voted_by_me(self, obj: Idea) -> bool:
        voter_ids = self.context.get("voted_idea_ids")
        return bool(voter_ids) and obj.id in voter_ids

    def get_application_status(self, obj: Idea) -> dict | None:
        # A hand-picked allowlist of exactly what an applicant should see about
        # their promoted application — never the raw DecisionOption (no reviewer
        # scores, no other applicants' internals), matching the discipline in
        # get_decision_template_key below.
        if not obj.promoted_to_option_id:
            return None
        option = obj.promoted_to_option
        return {
            "eligibility_status": option.eligibility_status,
            "eligibility_status_label": option.get_eligibility_status_display(),
            "eligibility_note": option.eligibility_note,
            "outcome_status": option.outcome_status,
            "outcome_status_label": option.get_outcome_status_display(),
            "awarded_amount": option.awarded_amount,
            "outcome_note": option.outcome_note,
        }


class IdeaCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(
        max_length=60, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    requested_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, default=None, min_value=0
    )


class IdeaCommentCreateSerializer(StrictSerializer):
    body = serializers.CharField(max_length=4000, trim_whitespace=True)


class IdeaArchiveSerializer(StrictSerializer):
    archived = serializers.BooleanField()


class SessionJoinSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()


class _IdeasFromContextMixin:
    """Render ideas from an explicitly-annotated queryset passed via context.

    The reverse `session.ideas` accessor can't carry the vote_count annotation
    or the requester-specific voted_by_me flag, so the view always supplies
    the already-annotated, already-filtered queryset as context["ideas"].
    """

    def get_ideas(self, obj):  # type: ignore[no-untyped-def]
        ideas = self.context.get("ideas", [])
        return IdeaSerializer(ideas, many=True, context=self.context).data


class OpenSessionPublicSerializer(_IdeasFromContextMixin, serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    ideas = serializers.SerializerMethodField()
    decision_template_key = serializers.SerializerMethodField()

    class Meta:
        model = OpenSession
        fields = [
            "id",
            "organisation_name",
            "title",
            "prompt",
            "description",
            "status",
            "status_label",
            "voting_enabled",
            "submission_deadline",
            "decision_template_key",
            "ideas",
        ]
        read_only_fields = fields

    def get_decision_template_key(self, obj: OpenSession) -> str | None:
        # Only the flavor, never the linked decision's title/content — this page is
        # reachable by anonymous visitors.
        return obj.decision.source_template_key if obj.decision_id else None


class OpenSessionSummarySerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    decision_title = serializers.CharField(source="decision.title", read_only=True, allow_null=True)
    decision_template_key = serializers.CharField(
        source="decision.source_template_key", read_only=True, allow_null=True
    )
    idea_count = serializers.IntegerField(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = OpenSession
        fields = [
            "id",
            "title",
            "prompt",
            "status",
            "status_label",
            "public_slug",
            "decision_id",
            "decision_title",
            "decision_template_key",
            "voting_enabled",
            "idea_count",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class OpenSessionOrganiserSerializer(_IdeasFromContextMixin, OpenSessionSummarySerializer):
    ideas = serializers.SerializerMethodField()

    class Meta(OpenSessionSummarySerializer.Meta):
        fields = OpenSessionSummarySerializer.Meta.fields + ["description", "ideas"]


class OpenSessionCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    prompt = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    decision_id = serializers.UUIDField(required=False, allow_null=True)
    default_workspace_id = serializers.UUIDField(required=False, allow_null=True)
    voting_enabled = serializers.BooleanField(required=False, default=True)
    submission_deadline = serializers.DateTimeField(required=False, allow_null=True)
