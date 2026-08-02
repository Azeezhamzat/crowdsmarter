# Generated explicitly for the Phase 4 vertical slice.

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
        ("participants", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Position",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("recommendation", models.CharField(choices=[("support", "Support"), ("support_with_conditions", "Support with conditions"), ("do_not_support_any", "Do not support any option"), ("abstain", "Abstain")], max_length=40)),
                ("rationale", models.TextField()),
                ("conditions", models.TextField(blank=True)),
                ("confidence", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], default="medium", max_length=20)),
                ("version", models.PositiveIntegerField()),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stakeholder_positions", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="stakeholder_positions", to="organisations.organisation")),
                ("participant", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="position_versions", to="participants.participant")),
                ("participant_role", models.CharField(choices=[("decision_owner", "Decision Owner"), ("decision_maker", "Decision Maker"), ("contributor", "Contributor"), ("reviewer", "Reviewer"), ("observer", "Observer")], max_length=30)),
                ("preferred_option", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="stakeholder_positions", to="decision_options.decisionoption")),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="submitted_positions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["participant__user__email", "-version", "id"]},
        ),
        migrations.AddConstraint(model_name="position", constraint=models.UniqueConstraint(fields=("decision", "participant", "version"), name="unique_position_version_per_participant")),
        migrations.AddConstraint(model_name="position", constraint=models.CheckConstraint(condition=models.Q(recommendation__in=["support", "support_with_conditions", "do_not_support_any", "abstain"]), name="position_recommendation_valid")),
        migrations.AddConstraint(model_name="position", constraint=models.CheckConstraint(condition=models.Q(confidence__in=["low", "medium", "high"]), name="position_confidence_valid")),
        migrations.AddConstraint(model_name="position", constraint=models.CheckConstraint(condition=models.Q(version__gte=1), name="position_version_positive")),
        migrations.AddIndex(model_name="position", index=models.Index(fields=["decision", "participant", "-version"], name="position_decision_person_idx")),
        migrations.AddIndex(model_name="position", index=models.Index(fields=["organisation", "-created_at"], name="position_org_created_idx")),
    ]
