# Generated explicitly for the Phase 3 vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("decision_options", "0001_initial"),
        ("decisions", "0001_initial"),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Evidence",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("summary", models.TextField()),
                ("source_type", models.CharField(choices=[("research", "Research"), ("internal_data", "Internal Data"), ("expert_judgement", "Expert Judgement"), ("stakeholder_input", "Stakeholder Input"), ("policy", "Policy or Regulation"), ("other", "Other")], max_length=40)),
                ("source_reference", models.CharField(blank=True, max_length=500)),
                ("source_url", models.URLField(blank=True, max_length=1000)),
                ("stance", models.CharField(choices=[("supports", "Supports"), ("challenges", "Challenges"), ("mixed", "Mixed"), ("context", "Context")], max_length=20)),
                ("strength", models.CharField(choices=[("low", "Low"), ("moderate", "Moderate"), ("high", "High")], default="moderate", max_length=20)),
                ("status", models.CharField(choices=[("active", "Active"), ("withdrawn", "Withdrawn")], default="active", max_length=20)),
                ("withdrawn_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_evidence_items", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence_items", to="decisions.decision")),
                ("option", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="evidence_items", to="decision_options.decisionoption")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="evidence_items", to="organisations.organisation")),
                ("withdrawn_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="withdrawn_evidence_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "title", "id"]},
        ),
        migrations.AddConstraint(model_name="evidence", constraint=models.CheckConstraint(condition=~models.Q(title=""), name="evidence_title_not_empty")),
        migrations.AddConstraint(model_name="evidence", constraint=models.CheckConstraint(condition=models.Q(source_type__in=["research", "internal_data", "expert_judgement", "stakeholder_input", "policy", "other"]), name="evidence_source_type_valid")),
        migrations.AddConstraint(model_name="evidence", constraint=models.CheckConstraint(condition=models.Q(stance__in=["supports", "challenges", "mixed", "context"]), name="evidence_stance_valid")),
        migrations.AddConstraint(model_name="evidence", constraint=models.CheckConstraint(condition=models.Q(strength__in=["low", "moderate", "high"]), name="evidence_strength_valid")),
        migrations.AddConstraint(model_name="evidence", constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "withdrawn"]), name="evidence_status_valid")),
        migrations.AddIndex(model_name="evidence", index=models.Index(fields=["decision", "status", "stance"], name="evidence_decision_idx")),
        migrations.AddIndex(model_name="evidence", index=models.Index(fields=["organisation", "status"], name="evidence_org_status_idx")),
    ]
