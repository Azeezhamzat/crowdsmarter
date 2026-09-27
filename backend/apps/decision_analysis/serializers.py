"""REST contracts for integrated decision analysis."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.serializers import DecisionUserSerializer

from .models import DecisionIssue, DecisionQualityReview, ExecutiveDecisionSummary
from .policies import can_edit_issue, can_manage_analysis


class DecisionIssueSerializer(serializers.ModelSerializer):
    owner = DecisionUserSerializer(read_only=True)
    created_by = DecisionUserSerializer(read_only=True)
    resolved_by = DecisionUserSerializer(read_only=True)
    issue_type_label = serializers.CharField(source="get_issue_type_display", read_only=True)
    severity_label = serializers.CharField(source="get_severity_display", read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = DecisionIssue
        fields = [
            "id",
            "decision_id",
            "option_id",
            "evidence_id",
            "assumption_id",
            "risk_id",
            "evaluation_exercise_id",
            "scenario_set_id",
            "issue_type",
            "issue_type_label",
            "title",
            "description",
            "severity",
            "severity_label",
            "status",
            "status_label",
            "owner",
            "due_date",
            "resolution",
            "resolved_at",
            "resolved_by",
            "created_by",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(request and can_edit_issue(actor=request.user, issue=obj))


class DecisionIssueWriteSerializer(StrictSerializer):
    option_id = serializers.UUIDField(required=False, allow_null=True)
    evidence_id = serializers.UUIDField(required=False, allow_null=True)
    assumption_id = serializers.UUIDField(required=False, allow_null=True)
    risk_id = serializers.UUIDField(required=False, allow_null=True)
    evaluation_exercise_id = serializers.UUIDField(required=False, allow_null=True)
    scenario_set_id = serializers.UUIDField(required=False, allow_null=True)
    issue_type = serializers.ChoiceField(choices=DecisionIssue.IssueType.choices)
    title = serializers.CharField(max_length=240)
    description = serializers.CharField(max_length=12000)
    severity = serializers.ChoiceField(
        choices=DecisionIssue.Severity.choices,
        required=False,
        default=DecisionIssue.Severity.MODERATE,
    )
    owner_id = serializers.UUIDField()
    due_date = serializers.DateField(required=False, allow_null=True)


class DecisionIssuePatchSerializer(StrictSerializer):
    title = serializers.CharField(max_length=240, required=False)
    description = serializers.CharField(max_length=12000, required=False)
    severity = serializers.ChoiceField(choices=DecisionIssue.Severity.choices, required=False)
    status = serializers.ChoiceField(choices=DecisionIssue.Status.choices, required=False)
    owner_id = serializers.UUIDField(required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    resolution = serializers.CharField(max_length=12000, required=False, allow_blank=True)

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        if attrs.get("status") == DecisionIssue.Status.RESOLVED and not attrs.get("resolution"):
            raise serializers.ValidationError({"resolution": "Record how the issue was resolved."})
        return attrs


QUALITY_KEYS = {
    "clear_question",
    "distinct_options",
    "status_quo_considered",
    "balanced_evidence",
    "explicit_assumptions",
    "stakeholders_represented",
    "uncertainty_examined",
    "scenarios_considered",
    "risks_addressed",
    "dissent_visible",
    "implementation_plausible",
    "review_timing_defined",
}


class QualityReviewSerializer(serializers.ModelSerializer):
    author = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    judgement_label = serializers.CharField(source="get_judgement_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = DecisionQualityReview
        fields = [
            "id",
            "decision_id",
            "version",
            "status",
            "status_label",
            "judgement",
            "judgement_label",
            "answers",
            "strengths",
            "blockers",
            "conditions",
            "author",
            "published_at",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and obj.status == DecisionQualityReview.Status.DRAFT
            and can_manage_analysis(actor=request.user, decision=obj.decision)
        )


class QualityReviewWriteSerializer(StrictSerializer):
    judgement = serializers.ChoiceField(
        choices=DecisionQualityReview.Judgement.choices,
        required=False,
        default=DecisionQualityReview.Judgement.NOT_READY,
    )
    answers = serializers.DictField(
        child=serializers.ChoiceField(choices=["yes", "partly", "no", "not_applicable"]),
        required=False,
        default=dict,
    )
    strengths = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, default=""
    )
    blockers = serializers.CharField(max_length=12000, required=False, allow_blank=True, default="")
    conditions = serializers.CharField(
        max_length=12000, required=False, allow_blank=True, default=""
    )

    def validate_answers(self, value):
        unknown = sorted(set(value) - QUALITY_KEYS)
        if unknown:
            raise serializers.ValidationError(
                f"Unknown quality-review questions: {', '.join(unknown)}"
            )
        return value


class QualityReviewPatchSerializer(QualityReviewWriteSerializer):
    judgement = serializers.ChoiceField(
        choices=DecisionQualityReview.Judgement.choices, required=False
    )
    answers = serializers.DictField(
        child=serializers.ChoiceField(choices=["yes", "partly", "no", "not_applicable"]),
        required=False,
    )
    strengths = serializers.CharField(max_length=12000, required=False, allow_blank=True)
    blockers = serializers.CharField(max_length=12000, required=False, allow_blank=True)
    conditions = serializers.CharField(max_length=12000, required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=[DecisionQualityReview.Status.PUBLISHED], required=False
    )


SUMMARY_FIELDS = [
    "context_summary",
    "options_summary",
    "evidence_summary",
    "uncertainty_summary",
    "stakeholder_summary",
    "scenario_summary",
    "evaluation_summary",
    "risk_summary",
    "unresolved_issues",
    "proposed_judgement",
    "conditions",
    "implementation_implications",
]


class ExecutiveSummarySerializer(serializers.ModelSerializer):
    created_by = DecisionUserSerializer(read_only=True)
    approved_by = DecisionUserSerializer(read_only=True)
    status_label = serializers.CharField(source="get_status_display", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = ExecutiveDecisionSummary
        fields = [
            "id",
            "decision_id",
            "version",
            "status",
            "status_label",
            *SUMMARY_FIELDS,
            "created_by",
            "approved_by",
            "approved_at",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_can_edit(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and obj.status == ExecutiveDecisionSummary.Status.DRAFT
            and can_manage_analysis(actor=request.user, decision=obj.decision)
        )


class ExecutiveSummaryWriteSerializer(StrictSerializer):
    context_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    options_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    evidence_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    uncertainty_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    stakeholder_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    scenario_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    evaluation_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    risk_summary = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    unresolved_issues = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    proposed_judgement = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    conditions = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )
    implementation_implications = serializers.CharField(
        max_length=16000, required=False, allow_blank=True, default=""
    )


class ExecutiveSummaryPatchSerializer(StrictSerializer):
    context_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    options_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    evidence_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    uncertainty_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    stakeholder_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    scenario_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    evaluation_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    risk_summary = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    unresolved_issues = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    proposed_judgement = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    conditions = serializers.CharField(max_length=16000, required=False, allow_blank=True)
    implementation_implications = serializers.CharField(
        max_length=16000, required=False, allow_blank=True
    )
    status = serializers.ChoiceField(
        choices=[ExecutiveDecisionSummary.Status.APPROVED],
        required=False,
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs
