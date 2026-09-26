"""API contracts for contribution orchestration."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import (
    ContributionPreference,
    ContributionRequest,
    ContributionReview,
    ContributionSubmission,
    FacilitationAgendaItem,
    FacilitationAuthorityResponse,
    FacilitationQualityReview,
    FacilitationRecord,
    FacilitationSession,
    SessionParticipant,
)
from .policies import (
    can_manage_contributions,
    can_review_request,
    can_work_on_request,
    has_contribution_authority,
)


class ContributionSubmissionSerializer(serializers.ModelSerializer):
    author = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ContributionSubmission
        fields = [
            "id",
            "request_id",
            "author",
            "sequence",
            "body",
            "references",
            "status",
            "status_label",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class ContributionReviewSerializer(serializers.ModelSerializer):
    reviewer = DecisionUserSerializer(read_only=True)
    outcome_label = serializers.CharField(source="get_outcome_display", read_only=True)

    class Meta:
        model = ContributionReview
        fields = [
            "id",
            "request_id",
            "submission_id",
            "reviewer",
            "outcome",
            "outcome_label",
            "note",
            "created_at",
        ]
        read_only_fields = fields


class SessionParticipantSerializer(serializers.ModelSerializer):
    user = DecisionUserSerializer(read_only=True)
    display_label = serializers.CharField(read_only=True)
    role_label = serializers.CharField(source="get_role_display", read_only=True)
    attendance_label = serializers.CharField(source="get_attendance_display", read_only=True)

    class Meta:
        model = SessionParticipant
        fields = [
            "id",
            "user",
            "display_label",
            "external_label",
            "stakeholder_group",
            "role",
            "role_label",
            "attendance",
            "attendance_label",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class FacilitationAgendaItemSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    actual_minutes = serializers.FloatField(read_only=True, allow_null=True)
    record_count = serializers.IntegerField(source="records.count", read_only=True)

    class Meta:
        model = FacilitationAgendaItem
        fields = [
            "id",
            "session_id",
            "title",
            "purpose",
            "method",
            "facilitator_prompt",
            "output_prompt",
            "planned_minutes",
            "actual_minutes",
            "order",
            "status",
            "status_label",
            "started_at",
            "ended_at",
            "record_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class FacilitationRecordSerializer(serializers.ModelSerializer):
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    channel_label = serializers.CharField(source="get_channel_display", read_only=True)
    origin_label = serializers.CharField(source="get_origin_display", read_only=True)
    attribution_label = serializers.CharField(source="get_attribution_display", read_only=True)
    source_participant = serializers.SerializerMethodField()
    created_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = FacilitationRecord
        fields = [
            "id",
            "session_id",
            "agenda_item_id",
            "kind",
            "kind_label",
            "body",
            "channel",
            "channel_label",
            "origin",
            "origin_label",
            "attribution",
            "attribution_label",
            "source_participant",
            "speaker_label",
            "permission_to_quote",
            "follow_up_owner",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields

    def get_source_participant(self, obj: FacilitationRecord):  # type: ignore[no-untyped-def]
        if not obj.source_participant_id:
            return None
        request = self.context.get("request")
        may_identify = obj.attribution != FacilitationRecord.Attribution.CONFIDENTIAL or bool(
            request
            and (
                obj.session.facilitator_id == request.user.id
                or has_contribution_authority(actor=request.user, decision=obj.decision)
            )
        )
        if not may_identify:
            return None
        return SessionParticipantSerializer(obj.source_participant).data

    def to_representation(self, instance):  # type: ignore[no-untyped-def]
        payload = super().to_representation(instance)
        request = self.context.get("request")
        may_identify = instance.attribution != FacilitationRecord.Attribution.CONFIDENTIAL or bool(
            request
            and (
                instance.session.facilitator_id == request.user.id
                or has_contribution_authority(actor=request.user, decision=instance.decision)
            )
        )
        if not may_identify:
            payload["speaker_label"] = ""
        return payload


class FacilitationAuthorityResponseSerializer(serializers.ModelSerializer):
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    published_by = DecisionUserSerializer(read_only=True)

    class Meta:
        model = FacilitationAuthorityResponse
        fields = [
            "id",
            "session_id",
            "what_we_heard",
            "what_changed",
            "what_did_not_change",
            "rationale",
            "next_steps",
            "status",
            "status_label",
            "published_at",
            "published_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class FacilitationQualityReviewSerializer(serializers.ModelSerializer):
    reviewed_by = DecisionUserSerializer(read_only=True)
    overall_score = serializers.FloatField(read_only=True)

    class Meta:
        model = FacilitationQualityReview
        fields = [
            "id",
            "session_id",
            "inclusion_score",
            "clarity_score",
            "neutrality_score",
            "participation_score",
            "follow_through_score",
            "overall_score",
            "what_worked",
            "improve_next_time",
            "unresolved_risks",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class FacilitationSessionSerializer(serializers.ModelSerializer):
    facilitator = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    participants = SessionParticipantSerializer(many=True, read_only=True)
    agenda_items = FacilitationAgendaItemSerializer(many=True, read_only=True)
    records = serializers.SerializerMethodField()
    authority_response = serializers.SerializerMethodField()
    quality_review = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    can_respond = serializers.SerializerMethodField()

    class Meta:
        model = FacilitationSession
        fields = [
            "id",
            "decision_id",
            "title",
            "objective",
            "agenda",
            "participation_guidance",
            "influence_boundary",
            "fixed_constraints",
            "participation_channels",
            "missing_perspectives",
            "accessibility_arrangements",
            "consent_boundary",
            "facilitator",
            "starts_at",
            "ends_at",
            "status",
            "status_label",
            "participants",
            "agenda_items",
            "records",
            "authority_response",
            "quality_review",
            "can_manage",
            "can_respond",
            "closed_at",
            "created_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_records(self, obj: FacilitationSession):  # type: ignore[no-untyped-def]
        return FacilitationRecordSerializer(obj.records.all(), many=True, context=self.context).data

    def get_authority_response(self, obj: FacilitationSession):  # type: ignore[no-untyped-def]
        try:
            response = obj.authority_response
        except FacilitationAuthorityResponse.DoesNotExist:
            return None
        request = self.context.get("request")
        if response.status == FacilitationAuthorityResponse.Status.DRAFT and not (
            request and has_contribution_authority(actor=request.user, decision=obj.decision)
        ):
            return None
        return FacilitationAuthorityResponseSerializer(response).data

    def get_quality_review(self, obj: FacilitationSession):  # type: ignore[no-untyped-def]
        try:
            review = obj.quality_review
        except FacilitationQualityReview.DoesNotExist:
            return None
        return FacilitationQualityReviewSerializer(review).data

    def get_can_manage(self, obj: FacilitationSession) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and (
                obj.facilitator_id == request.user.id
                or can_manage_contributions(actor=request.user, decision=obj.decision)
            )
        )

    def get_can_respond(self, obj: FacilitationSession) -> bool:
        request = self.context.get("request")
        return bool(
            request and has_contribution_authority(actor=request.user, decision=obj.decision)
        )


class ContributionRequestSerializer(serializers.ModelSerializer):
    organisation_name = serializers.CharField(source="organisation.name", read_only=True)
    decision_title = serializers.CharField(source="decision.title", read_only=True)
    session_title = serializers.CharField(source="session.title", read_only=True, allow_null=True)
    assignee = DecisionUserSerializer(read_only=True)
    reviewer = DecisionUserSerializer(read_only=True)
    requested_by = DecisionUserSerializer(read_only=True)
    kind_label = serializers.CharField(source="get_kind_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    priority_label = serializers.CharField(source="get_priority_display", read_only=True)
    submissions = serializers.SerializerMethodField()
    reviews = ContributionReviewSerializer(many=True, read_only=True)
    can_work = serializers.SerializerMethodField()
    can_review = serializers.SerializerMethodField()
    can_manage = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = ContributionRequest
        fields = [
            "id",
            "organisation_id",
            "organisation_name",
            "decision_id",
            "decision_title",
            "option_id",
            "session_id",
            "session_title",
            "requested_by",
            "assignee",
            "reviewer",
            "kind",
            "kind_label",
            "title",
            "instructions",
            "priority",
            "priority_label",
            "status",
            "status_label",
            "due_at",
            "opened_at",
            "submitted_at",
            "reviewed_at",
            "completed_at",
            "cancelled_at",
            "submissions",
            "reviews",
            "can_work",
            "can_review",
            "can_manage",
            "is_overdue",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_submissions(self, obj: ContributionRequest):  # type: ignore[no-untyped-def]
        request = self.context.get("request")
        items = list(obj.submissions.all())
        if not request:
            return []
        has_authority = has_contribution_authority(actor=request.user, decision=obj.decision)
        if (
            not has_authority
            and obj.assignee_id != request.user.id
            and obj.reviewer_id != request.user.id
        ):
            items = [
                item for item in items if item.status == ContributionSubmission.Status.SUBMITTED
            ]
        return ContributionSubmissionSerializer(items, many=True).data

    def get_can_work(self, obj: ContributionRequest) -> bool:
        request = self.context.get("request")
        return bool(request and can_work_on_request(actor=request.user, request=obj))

    def get_can_review(self, obj: ContributionRequest) -> bool:
        request = self.context.get("request")
        return bool(request and can_review_request(actor=request.user, request=obj))

    def get_can_manage(self, obj: ContributionRequest) -> bool:
        request = self.context.get("request")
        return bool(request and can_manage_contributions(actor=request.user, decision=obj.decision))

    def get_is_overdue(self, obj: ContributionRequest) -> bool:
        from django.utils import timezone

        return bool(
            obj.due_at
            and obj.due_at < timezone.now()
            and obj.status
            not in {ContributionRequest.Status.ACCEPTED, ContributionRequest.Status.CANCELLED}
        )


class ContributionRequestCreateSerializer(StrictSerializer):
    assignee_id = serializers.UUIDField()
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    kind = serializers.ChoiceField(choices=ContributionRequest.Kind.choices)
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    instructions = serializers.CharField(max_length=12000, trim_whitespace=True)
    priority = serializers.ChoiceField(
        choices=ContributionRequest.Priority.choices,
        default=ContributionRequest.Priority.NORMAL,
    )
    due_at = serializers.DateTimeField(required=False, allow_null=True)
    option_id = serializers.UUIDField(required=False, allow_null=True)
    session_id = serializers.UUIDField(required=False, allow_null=True)
    open_immediately = serializers.BooleanField(default=True)


class ContributionRequestUpdateSerializer(StrictSerializer):
    assignee_id = serializers.UUIDField(required=False)
    reviewer_id = serializers.UUIDField(required=False, allow_null=True)
    title = serializers.CharField(max_length=240, required=False, trim_whitespace=True)
    instructions = serializers.CharField(max_length=12000, required=False, trim_whitespace=True)
    priority = serializers.ChoiceField(choices=ContributionRequest.Priority.choices, required=False)
    due_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one assignment field to update.")
        return attrs


class ContributionRequestActionSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=["open", "start", "start_review", "cancel"])
    reason = serializers.CharField(
        max_length=4000, required=False, allow_blank=True, trim_whitespace=True
    )


class ContributionDraftSerializer(StrictSerializer):
    body = serializers.CharField(max_length=30000, trim_whitespace=True)
    references = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )


class ContributionReviewInputSerializer(StrictSerializer):
    outcome = serializers.ChoiceField(choices=ContributionReview.Outcome.choices)
    note = serializers.CharField(max_length=12000, trim_whitespace=True)


class FacilitationParticipantInputSerializer(StrictSerializer):
    user_id = serializers.UUIDField()
    role = serializers.ChoiceField(
        choices=SessionParticipant.Role.choices,
        required=False,
        default=SessionParticipant.Role.PARTICIPANT,
    )


class FacilitationExternalParticipantInputSerializer(StrictSerializer):
    external_label = serializers.CharField(max_length=240, trim_whitespace=True)
    stakeholder_group = serializers.CharField(
        max_length=240, required=False, allow_blank=True, trim_whitespace=True
    )
    role = serializers.ChoiceField(
        choices=SessionParticipant.Role.choices,
        required=False,
        default=SessionParticipant.Role.PARTICIPANT,
    )


class FacilitationAgendaItemInputSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    purpose = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    method = serializers.CharField(
        max_length=240, required=False, allow_blank=True, trim_whitespace=True
    )
    facilitator_prompt = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    output_prompt = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    planned_minutes = serializers.IntegerField(min_value=1, max_value=480, default=10)


class FacilitationSessionCreateSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, trim_whitespace=True)
    objective = serializers.CharField(max_length=12000, trim_whitespace=True)
    agenda = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    participation_guidance = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    influence_boundary = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    fixed_constraints = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    participation_channels = serializers.ListField(
        child=serializers.ChoiceField(choices=FacilitationSession.Channel.choices),
        required=False,
        allow_empty=True,
    )
    missing_perspectives = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    accessibility_arrangements = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    consent_boundary = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, trim_whitespace=True
    )
    facilitator_id = serializers.UUIDField(required=False, allow_null=True)
    starts_at = serializers.DateTimeField(required=False, allow_null=True)
    ends_at = serializers.DateTimeField(required=False, allow_null=True)
    participant_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, allow_empty=True
    )
    participants = FacilitationParticipantInputSerializer(
        many=True, required=False, allow_empty=True
    )
    external_participants = FacilitationExternalParticipantInputSerializer(
        many=True, required=False, allow_empty=True
    )
    agenda_items = FacilitationAgendaItemInputSerializer(
        many=True, required=False, allow_empty=True
    )


class FacilitationSessionStatusSerializer(StrictSerializer):
    status = serializers.ChoiceField(choices=FacilitationSession.Status.choices)


class FacilitationAgendaItemCreateSerializer(FacilitationAgendaItemInputSerializer):
    pass


class FacilitationAgendaItemActionSerializer(StrictSerializer):
    action = serializers.ChoiceField(choices=["start", "complete", "skip", "reset"])


class FacilitationRecordCreateSerializer(StrictSerializer):
    kind = serializers.ChoiceField(choices=FacilitationRecord.Kind.choices)
    body = serializers.CharField(max_length=30000, trim_whitespace=True)
    channel = serializers.ChoiceField(choices=FacilitationRecord.Channel.choices)
    origin = serializers.ChoiceField(choices=FacilitationRecord.Origin.choices)
    attribution = serializers.ChoiceField(
        choices=FacilitationRecord.Attribution.choices,
        default=FacilitationRecord.Attribution.ANONYMOUS,
    )
    source_participant_id = serializers.UUIDField(required=False, allow_null=True)
    agenda_item_id = serializers.UUIDField(required=False, allow_null=True)
    speaker_label = serializers.CharField(
        max_length=240, required=False, allow_blank=True, trim_whitespace=True
    )
    permission_to_quote = serializers.BooleanField(default=False)
    follow_up_owner = serializers.CharField(
        max_length=240, required=False, allow_blank=True, trim_whitespace=True
    )


class FacilitationAuthorityResponseUpdateSerializer(StrictSerializer):
    what_we_heard = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )
    what_changed = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )
    what_did_not_change = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )
    rationale = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )
    next_steps = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )
    publish = serializers.BooleanField(default=False)


class FacilitationQualityReviewInputSerializer(StrictSerializer):
    inclusion_score = serializers.IntegerField(min_value=1, max_value=5)
    clarity_score = serializers.IntegerField(min_value=1, max_value=5)
    neutrality_score = serializers.IntegerField(min_value=1, max_value=5)
    participation_score = serializers.IntegerField(min_value=1, max_value=5)
    follow_through_score = serializers.IntegerField(min_value=1, max_value=5)
    what_worked = serializers.CharField(max_length=30000, trim_whitespace=True)
    improve_next_time = serializers.CharField(max_length=30000, trim_whitespace=True)
    unresolved_risks = serializers.CharField(
        max_length=30000, required=False, allow_blank=True, trim_whitespace=True
    )


class SessionAttendanceSerializer(StrictSerializer):
    attendance = serializers.ChoiceField(choices=SessionParticipant.Attendance.choices)


class ContributionPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContributionPreference
        fields = [
            "id",
            "organisation_id",
            "digest_cadence",
            "email_enabled",
            "due_reminders_enabled",
            "reminder_days_before",
            "last_digest_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organisation_id", "last_digest_at", "created_at", "updated_at"]


class ContributionPreferenceUpdateSerializer(StrictSerializer):
    digest_cadence = serializers.ChoiceField(choices=ContributionPreference.DigestCadence.choices)
    email_enabled = serializers.BooleanField()
    due_reminders_enabled = serializers.BooleanField()
    reminder_days_before = serializers.IntegerField(min_value=0, max_value=30)
