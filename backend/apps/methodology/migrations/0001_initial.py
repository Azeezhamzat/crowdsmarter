# Generated for CrowdSmarter Phase 17.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0002_administration_and_membership_history"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionMethod",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("key", models.SlugField(max_length=80)),
                ("name", models.CharField(max_length=200)),
                ("summary", models.TextField()),
                ("best_for", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("approved", "Approved"), ("retired", "Retired")], default="draft", max_length=20)),
                ("retired_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decision_methods", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_methods", to="organisations.organisation")),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="DecisionMethodVersion",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("version", models.PositiveSmallIntegerField()),
                ("status", models.CharField(choices=[("draft", "Draft"), ("approved", "Approved"), ("retired", "Retired")], default="draft", max_length=20)),
                ("question_prompt", models.TextField()),
                ("purpose_prompt", models.TextField()),
                ("context_prompt", models.TextField()),
                ("scope_prompt", models.TextField()),
                ("contribution_prompt", models.TextField()),
                ("suggested_urgency", models.CharField(choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")], default="normal", max_length=20)),
                ("required_fields", models.JSONField(blank=True, default=list)),
                ("checklist", models.JSONField(blank=True, default=list)),
                ("evidence_prompts", models.JSONField(blank=True, default=list)),
                ("assumption_prompts", models.JSONField(blank=True, default=list)),
                ("risk_prompts", models.JSONField(blank=True, default=list)),
                ("stakeholder_prompts", models.JSONField(blank=True, default=list)),
                ("lifecycle_expectations", models.JSONField(blank=True, default=list)),
                ("cloned_from_builtin_key", models.CharField(blank=True, max_length=80)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approved_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="approved_decision_method_versions", to=settings.AUTH_USER_MODEL)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decision_method_versions", to=settings.AUTH_USER_MODEL)),
                ("method", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="versions", to="methodology.decisionmethod")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_method_versions", to="organisations.organisation")),
            ],
            options={"ordering": ["method__name", "-version", "id"]},
        ),
        migrations.AddField(
            model_name="decisionmethod", name="current_version",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="current_for_methods", to="methodology.decisionmethodversion"),
        ),
        migrations.AddConstraint(model_name="decisionmethod", constraint=models.UniqueConstraint(fields=("organisation", "key"), name="unique_method_key_per_org")),
        migrations.AddConstraint(model_name="decisionmethod", constraint=models.CheckConstraint(condition=models.Q(status__in=["draft", "approved", "retired"]), name="decision_method_status_valid")),
        migrations.AddConstraint(model_name="decisionmethod", constraint=models.CheckConstraint(condition=~models.Q(name=""), name="decision_method_name_not_empty")),
        migrations.AddConstraint(model_name="decisionmethod", constraint=models.CheckConstraint(condition=~models.Q(summary=""), name="decision_method_summary_not_empty")),
        migrations.AddIndex(model_name="decisionmethod", index=models.Index(fields=["organisation", "status", "name"], name="method_org_status_idx")),
        migrations.AddConstraint(model_name="decisionmethodversion", constraint=models.UniqueConstraint(fields=("method", "version"), name="unique_version_per_method")),
        migrations.AddConstraint(model_name="decisionmethodversion", constraint=models.CheckConstraint(condition=models.Q(status__in=["draft", "approved", "retired"]), name="decision_method_version_status_valid")),
        migrations.AddConstraint(model_name="decisionmethodversion", constraint=models.CheckConstraint(condition=models.Q(suggested_urgency__in=["low", "normal", "high", "critical"]), name="decision_method_urgency_valid")),
        migrations.AddIndex(model_name="decisionmethodversion", index=models.Index(fields=["organisation", "status", "-version"], name="method_ver_org_status_idx")),
    ]
