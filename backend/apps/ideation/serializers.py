"""Read/write representations for open sessions, ideas, and votes."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import Idea, IdeaComment, IdeaTeamMember, OpenSession, SessionParticipant


class SessionParticipantSerializer(serializers.Serializer):
    name = serializers.CharField()


class IdeaTeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdeaTeamMember
        fields = ["id", "name", "role"]
        read_only_fields = fields


class IdeaTeamMemberInputSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    role = serializers.CharField(
        max_length=60, trim_whitespace=True, allow_blank=True, required=False, default=""
    )


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
    comments = IdeaCommentSerializer(many=True, read_only=True)
    team_members = IdeaTeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = Idea
        fields = [
            "id",
            "title",
            "description",
            "category",
            "requested_amount",
            "team_name",
            "team_members",
            "status",
            "status_label",
            "submitted_by_participant",
            "submitted_by_user",
            "vote_count",
            "voted_by_me",
            "comments",
            "created_at",
        ]
        read_only_fields = fields

    def get_voted_by_me(self, obj: Idea) -> bool:
        voter_ids = self.context.get("voted_idea_ids")
        return isinstance(voter_ids, set) and obj.id in voter_ids


class IdeaOrganiserSerializer(IdeaSerializer):
    """Adds submitter safeguarding fields visible only to authenticated organisers.

    Never used on the public idea feed - a minor's school, age bracket, and
    guardian-consent status are not for anonymous visitors to see.
    """

    submitter_school = serializers.SerializerMethodField()
    submitter_age_bracket = serializers.SerializerMethodField()
    submitter_age_bracket_label = serializers.SerializerMethodField()
    submitter_guardian_consent_given = serializers.SerializerMethodField()
    application_status = serializers.SerializerMethodField()

    class Meta(IdeaSerializer.Meta):
        fields = IdeaSerializer.Meta.fields + [
            "application_status",
            "submitter_school",
            "submitter_age_bracket",
            "submitter_age_bracket_label",
            "submitter_guardian_consent_given",
        ]
        read_only_fields = fields

    def get_application_status(self, obj: Idea) -> dict | None:
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

    def get_submitter_school(self, obj: Idea) -> str | None:
        participant = obj.submitted_by_participant
        return participant.school_name if participant else None

    def get_submitter_age_bracket(self, obj: Idea) -> str | None:
        participant = obj.submitted_by_participant
        return participant.age_bracket if participant else None

    def get_submitter_age_bracket_label(self, obj: Idea) -> str | None:
        participant = obj.submitted_by_participant
        if not participant or not participant.age_bracket:
            return None
        return participant.get_age_bracket_display()

    def get_submitter_guardian_consent_given(self, obj: Idea) -> bool | None:
        participant = obj.submitted_by_participant
        if not participant or not participant.is_declared_minor:
            return None
        return participant.guardian_consent_given


class IdeaCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    category = serializers.CharField(
        max_length=60, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    requested_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, required=False, allow_null=True, default=None, min_value=0
    )
    team_name = serializers.CharField(
        max_length=200, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    team_members = IdeaTeamMemberInputSerializer(many=True, required=False, default=list)

    def validate_team_members(self, value: list[dict]) -> list[dict]:
        if len(value) > 12:
            raise serializers.ValidationError("A team roster may list at most 12 people.")
        return value


class IdeaCommentCreateSerializer(StrictSerializer):
    body = serializers.CharField(max_length=4000, trim_whitespace=True)


class IdeaArchiveSerializer(StrictSerializer):
    archived = serializers.BooleanField()


class SessionJoinSerializer(StrictSerializer):
    name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    school_name = serializers.CharField(
        max_length=200, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    age_bracket = serializers.ChoiceField(
        choices=SessionParticipant.AgeBracket.choices, allow_blank=True, required=False, default=""
    )
    guardian_name = serializers.CharField(
        max_length=200, trim_whitespace=True, allow_blank=True, required=False, default=""
    )
    guardian_email = serializers.EmailField(allow_blank=True, required=False, default="")
    guardian_consent_given = serializers.BooleanField(required=False, default=False)


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
            "requires_guardian_consent",
            "team_submissions_enabled",
            "decision_template_key",
            "ideas",
        ]
        read_only_fields = fields

    def get_decision_template_key(self, obj: OpenSession) -> str | None:
        # Only the flavor, never the linked decision's title/content - this page is
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
            "requires_guardian_consent",
            "team_submissions_enabled",
            "idea_count",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class OpenSessionOrganiserSerializer(_IdeasFromContextMixin, OpenSessionSummarySerializer):
    ideas = serializers.SerializerMethodField()

    class Meta(OpenSessionSummarySerializer.Meta):
        fields = OpenSessionSummarySerializer.Meta.fields + ["description", "ideas"]

    def get_ideas(self, obj):  # type: ignore[no-untyped-def]
        ideas = self.context.get("ideas", [])
        return IdeaOrganiserSerializer(ideas, many=True, context=self.context).data


class OpenSessionCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240)
    prompt = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True, default="")
    decision_id = serializers.UUIDField(required=False, allow_null=True)
    default_workspace_id = serializers.UUIDField(required=False, allow_null=True)
    voting_enabled = serializers.BooleanField(required=False, default=True)
    submission_deadline = serializers.DateTimeField(required=False, allow_null=True)
    requires_guardian_consent = serializers.BooleanField(required=False, default=False)
    team_submissions_enabled = serializers.BooleanField(required=False, default=False)
