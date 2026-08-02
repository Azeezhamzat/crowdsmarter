# Generated for CrowdSmarter Phase 15.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
        ("decisions", "0003_decision_template_provenance"),
        ("decision_options", "0001_initial"),
        ("evidence", "0002_evidence_structured_source"),
        ("assumptions", "0001_initial"),
        ("risks", "0001_initial"),
        ("evaluations", "0001_initial"),
        ("foresight", "0004_scenario_planning"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionQualityReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published"), ("superseded", "Superseded")], default="draft", max_length=20)),
                ("judgement", models.CharField(choices=[("not_ready", "Not ready"), ("ready_with_conditions", "Ready with conditions"), ("ready", "Ready")], default="not_ready", max_length=30)),
                ("answers", models.JSONField(default=dict)),
                ("strengths", models.TextField(blank=True)),
                ("blockers", models.TextField(blank=True)),
                ("conditions", models.TextField(blank=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("author", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="authored_decision_quality_reviews", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="quality_reviews", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_quality_reviews", to="organisations.organisation")),
            ],
            options={"ordering": ["-version", "-created_at"]},
        ),
        migrations.CreateModel(
            name="ExecutiveDecisionSummary",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version", models.PositiveIntegerField()),
                ("status", models.CharField(choices=[("draft", "Draft"), ("approved", "Approved"), ("superseded", "Superseded")], default="draft", max_length=20)),
                ("context_summary", models.TextField(blank=True)),
                ("options_summary", models.TextField(blank=True)),
                ("evidence_summary", models.TextField(blank=True)),
                ("uncertainty_summary", models.TextField(blank=True)),
                ("stakeholder_summary", models.TextField(blank=True)),
                ("scenario_summary", models.TextField(blank=True)),
                ("evaluation_summary", models.TextField(blank=True)),
                ("risk_summary", models.TextField(blank=True)),
                ("unresolved_issues", models.TextField(blank=True)),
                ("proposed_judgement", models.TextField(blank=True)),
                ("conditions", models.TextField(blank=True)),
                ("implementation_implications", models.TextField(blank=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_executive_decision_summaries", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_executive_decision_summaries", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="executive_summaries", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="executive_decision_summaries", to="organisations.organisation")),
            ],
            options={"ordering": ["-version", "-created_at"]},
        ),
        migrations.CreateModel(
            name="DecisionIssue",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("issue_type", models.CharField(choices=[("evidence_contradiction", "Evidence contradiction"), ("missing_evidence", "Missing evidence"), ("unsupported_assumption", "Unsupported assumption"), ("stakeholder_gap", "Stakeholder gap"), ("unresolved_objection", "Unresolved objection"), ("scenario_vulnerability", "Scenario vulnerability"), ("resource_uncertainty", "Resource uncertainty"), ("implementation_uncertainty", "Implementation uncertainty"), ("other", "Other")], max_length=40)),
                ("title", models.CharField(max_length=240)),
                ("description", models.TextField()),
                ("severity", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High"), ("critical", "Critical")], default="moderate", max_length=20)),
                ("status", models.CharField(choices=[("open", "Open"), ("in_progress", "In progress"), ("resolved", "Resolved"), ("dismissed", "Dismissed")], default="open", max_length=20)),
                ("due_date", models.DateField(blank=True, null=True)),
                ("resolution", models.TextField(blank=True)),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("assumption", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="assumptions.assumption")),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decision_analysis_issues", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="analysis_issues", to="decisions.decision")),
                ("evaluation_exercise", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="evaluations.evaluationexercise")),
                ("evidence", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="evidence.evidence")),
                ("option", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="decision_options.decisionoption")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_analysis_issues", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_decision_analysis_issues", to=settings.AUTH_USER_MODEL)),
                ("resolved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="resolved_decision_analysis_issues", to=settings.AUTH_USER_MODEL)),
                ("risk", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="risks.risk")),
                ("scenario_set", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="analysis_issues", to="foresight.scenarioset")),
            ],
            options={"ordering": ["status", "due_date", "created_at"]},
        ),
        migrations.AddConstraint(model_name="decisionqualityreview", constraint=models.UniqueConstraint(fields=("decision", "version"), name="unique_quality_review_version")),
        migrations.AddConstraint(model_name="decisionqualityreview", constraint=models.UniqueConstraint(condition=models.Q(("status", "draft")), fields=("decision",), name="one_draft_quality_review")),
        migrations.AddConstraint(model_name="decisionqualityreview", constraint=models.UniqueConstraint(condition=models.Q(("status", "published")), fields=("decision",), name="one_published_quality_review")),
        migrations.AddConstraint(model_name="decisionqualityreview", constraint=models.CheckConstraint(condition=models.Q(("version__gte", 1)), name="quality_review_version_positive")),
        migrations.AddConstraint(model_name="executivedecisionsummary", constraint=models.UniqueConstraint(fields=("decision", "version"), name="unique_executive_summary_version")),
        migrations.AddConstraint(model_name="executivedecisionsummary", constraint=models.UniqueConstraint(condition=models.Q(("status", "draft")), fields=("decision",), name="one_draft_executive_summary")),
        migrations.AddConstraint(model_name="executivedecisionsummary", constraint=models.UniqueConstraint(condition=models.Q(("status", "approved")), fields=("decision",), name="one_approved_executive_summary")),
        migrations.AddConstraint(model_name="executivedecisionsummary", constraint=models.CheckConstraint(condition=models.Q(("version__gte", 1)), name="executive_summary_version_positive")),
        migrations.AddIndex(model_name="decisionissue", index=models.Index(fields=["decision", "status", "severity"], name="analysis_issue_decision_idx")),
        migrations.AddIndex(model_name="decisionissue", index=models.Index(fields=["organisation", "status"], name="analysis_issue_org_idx")),
    ]
