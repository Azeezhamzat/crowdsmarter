"""API contracts for organisation-owned decision methods."""

from rest_framework import serializers

from apps.core.serializers import StrictSerializer
from apps.decisions.templates import list_templates

from .models import DecisionMethod, DecisionMethodUsage, DecisionMethodVersion


class MethodVersionSerializer(serializers.ModelSerializer):
    approved_by_email = serializers.EmailField(source="approved_by.email", read_only=True, allow_null=True)

    class Meta:
        model = DecisionMethodVersion
        fields = [
            "id", "method_id", "organisation_id", "version", "status", "question_prompt",
            "purpose_prompt", "context_prompt", "scope_prompt", "contribution_prompt",
            "suggested_urgency", "required_fields", "checklist", "evidence_prompts",
            "assumption_prompts", "risk_prompts", "stakeholder_prompts", "lifecycle_expectations",
            "cloned_from_builtin_key", "approved_by_email", "approved_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class DecisionMethodSerializer(serializers.ModelSerializer):
    current_version = MethodVersionSerializer(read_only=True)
    versions = MethodVersionSerializer(many=True, read_only=True)

    class Meta:
        model = DecisionMethod
        fields = [
            "id", "organisation_id", "key", "name", "summary", "best_for", "status",
            "current_version", "versions", "retired_at", "created_at", "updated_at",
        ]
        read_only_fields = fields


class MethodVersionInputSerializer(StrictSerializer):
    question_prompt = serializers.CharField(max_length=8000, trim_whitespace=True)
    purpose_prompt = serializers.CharField(max_length=8000, trim_whitespace=True)
    context_prompt = serializers.CharField(max_length=8000, trim_whitespace=True)
    scope_prompt = serializers.CharField(max_length=8000, trim_whitespace=True)
    contribution_prompt = serializers.CharField(max_length=8000, trim_whitespace=True)
    suggested_urgency = serializers.ChoiceField(choices=["low", "normal", "high", "critical"], default="normal")
    required_fields = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            "decision_question", "purpose", "context", "scope", "contribution_guidance"
        ]), required=False, default=list
    )
    checklist = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    evidence_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    assumption_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    risk_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    stakeholder_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)
    lifecycle_expectations = serializers.ListField(child=serializers.CharField(max_length=500), required=False, default=list)


class MethodCreateSerializer(MethodVersionInputSerializer):
    name = serializers.CharField(max_length=200, trim_whitespace=True)
    summary = serializers.CharField(max_length=4000, trim_whitespace=True)
    best_for = serializers.CharField(max_length=4000, trim_whitespace=True, allow_blank=True, required=False, default="")


class MethodCloneSerializer(StrictSerializer):
    builtin_key = serializers.ChoiceField(choices=[item["key"] for item in list_templates()])
    name = serializers.CharField(max_length=200, trim_whitespace=True, allow_blank=True, required=False, default="")


class MethodVersionUpdateSerializer(StrictSerializer):
    question_prompt = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    purpose_prompt = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    context_prompt = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    scope_prompt = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    contribution_prompt = serializers.CharField(max_length=8000, trim_whitespace=True, required=False)
    suggested_urgency = serializers.ChoiceField(choices=["low", "normal", "high", "critical"], required=False)
    required_fields = serializers.ListField(child=serializers.ChoiceField(choices=[
        "decision_question", "purpose", "context", "scope", "contribution_guidance"
    ]), required=False)
    checklist = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    evidence_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    assumption_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    risk_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    stakeholder_prompts = serializers.ListField(child=serializers.CharField(max_length=500), required=False)
    lifecycle_expectations = serializers.ListField(child=serializers.CharField(max_length=500), required=False)

    def validate(self, attrs):  # type: ignore[no-untyped-def]
        if not attrs:
            raise serializers.ValidationError("Provide at least one field to update.")
        return attrs


class MethodRetireSerializer(StrictSerializer):
    reason = serializers.CharField(max_length=4000, trim_whitespace=True)


class MethodUsageSerializer(serializers.ModelSerializer):
    method_name = serializers.CharField(source="method_version.method.name", read_only=True)
    method_version_number = serializers.IntegerField(source="method_version.version", read_only=True)
    decision_title = serializers.CharField(source="decision.title", read_only=True)
    applied_by_email = serializers.EmailField(source="applied_by.email", read_only=True)

    class Meta:
        model = DecisionMethodUsage
        fields = [
            "id", "organisation_id", "method_version_id", "method_name", "method_version_number",
            "decision_id", "decision_title", "applied_by_email", "created_at",
        ]
        read_only_fields = fields
