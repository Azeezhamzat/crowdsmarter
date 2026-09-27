"""Read/write representations for the applicant portal."""

from __future__ import annotations

from rest_framework import serializers

from apps.core.serializers import StrictSerializer

from .models import ProgressReport


class MagicLinkRequestSerializer(StrictSerializer):
    email = serializers.EmailField()
    name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")


class MagicLinkConsumeSerializer(StrictSerializer):
    token = serializers.CharField()


class ProgressReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProgressReport
        fields = ["id", "body", "created_at"]
        read_only_fields = fields


class ProgressReportCreateSerializer(StrictSerializer):
    body = serializers.CharField(max_length=8000, trim_whitespace=True)


class ApplicationOutcomeSerializer(serializers.Serializer):
    eligibility_status = serializers.CharField()
    eligibility_status_label = serializers.CharField()
    outcome_status = serializers.CharField()
    outcome_status_label = serializers.CharField()
    awarded_amount = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    outcome_note = serializers.CharField()


class MyApplicationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    status = serializers.CharField()
    status_label = serializers.CharField(source="get_status_display")
    requested_amount = serializers.DecimalField(max_digits=14, decimal_places=2, allow_null=True)
    session_title = serializers.CharField(source="session.title")
    organisation_name = serializers.CharField(source="session.organisation.name")
    created_at = serializers.DateTimeField()
    outcome = serializers.SerializerMethodField()
    can_submit_progress_report = serializers.SerializerMethodField()
    progress_reports = serializers.SerializerMethodField()

    def get_outcome(self, obj) -> dict | None:  # type: ignore[no-untyped-def]
        if not obj.promoted_to_option_id:
            return None
        option = obj.promoted_to_option
        return ApplicationOutcomeSerializer(
            {
                "eligibility_status": option.eligibility_status,
                "eligibility_status_label": option.get_eligibility_status_display(),
                "outcome_status": option.outcome_status,
                "outcome_status_label": option.get_outcome_status_display(),
                "awarded_amount": option.awarded_amount,
                "outcome_note": option.outcome_note,
            }
        ).data

    def get_can_submit_progress_report(self, obj) -> bool:  # type: ignore[no-untyped-def]
        return bool(obj.promoted_to_option_id and obj.promoted_to_option.outcome_status == "funded")

    def get_progress_reports(self, obj) -> list[dict]:  # type: ignore[no-untyped-def]
        reports = self.context.get("progress_reports_by_idea", {}).get(obj.id, [])
        return [dict(item) for item in ProgressReportSerializer(reports, many=True).data]
