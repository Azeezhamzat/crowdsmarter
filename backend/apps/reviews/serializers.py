"""API contracts for commitment, implementation, and outcome review."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.models import Decision
from apps.decisions.serializers import DecisionUserSerializer

from .models import DecisionReview


class DecisionReviewSerializer(serializers.ModelSerializer):
    implementation_owner = DecisionUserSerializer(read_only=True)
    commitment_recorded_by = DecisionUserSerializer(read_only=True)
    implementation_started_by = DecisionUserSerializer(read_only=True)
    reviewed_by = DecisionUserSerializer(read_only=True)
    outcome_assessment_label = serializers.CharField(
        source="get_outcome_assessment_display",
        read_only=True,
    )

    class Meta:
        model = DecisionReview
        fields = [
            "id",
            "decision_id",
            "implementation_owner",
            "commitment_statement",
            "success_measures",
            "review_due_date",
            "commitment_rationale",
            "commitment_recorded_by",
            "commitment_recorded_at",
            "implementation_plan",
            "implementation_started_by",
            "implementation_started_at",
            "implementation_summary",
            "outcome_summary",
            "outcome_assessment",
            "outcome_assessment_label",
            "review_evidence",
            "unintended_consequences",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CommitmentInputSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    implementation_owner_id = serializers.UUIDField()
    commitment_statement = serializers.CharField(max_length=12000, trim_whitespace=True)
    success_measures = serializers.CharField(max_length=12000, trim_whitespace=True)
    review_due_date = serializers.DateField()
    rationale = serializers.CharField(max_length=8000, trim_whitespace=True)


class ImplementationStartInputSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    implementation_plan = serializers.CharField(max_length=16000, trim_whitespace=True)
    rationale = serializers.CharField(max_length=8000, trim_whitespace=True)


class OutcomeReviewOpenInputSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    implementation_summary = serializers.CharField(max_length=16000, trim_whitespace=True)
    rationale = serializers.CharField(max_length=8000, trim_whitespace=True)


class OutcomeReviewCompleteInputSerializer(StrictSerializer):
    expected_status = serializers.ChoiceField(choices=Decision.Status.choices)
    outcome_summary = serializers.CharField(max_length=16000, trim_whitespace=True)
    outcome_assessment = serializers.ChoiceField(
        choices=DecisionReview.OutcomeAssessment.choices
    )
    review_evidence = serializers.CharField(max_length=16000, trim_whitespace=True)
    unintended_consequences = serializers.CharField(
        max_length=12000,
        trim_whitespace=True,
        allow_blank=True,
        required=False,
        default="",
    )
    rationale = serializers.CharField(max_length=8000, trim_whitespace=True)


class ImplementationOwnerInputSerializer(StrictSerializer):
    implementation_owner_id = serializers.UUIDField()
