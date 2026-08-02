# Generated manually for the Phase 2 vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
        ("workspaces", "0002_seed_default_workspaces"),
    ]

    operations = [
        migrations.CreateModel(
            name="Decision",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("decision_question", models.TextField(blank=True)),
                ("purpose", models.TextField(blank=True)),
                ("context", models.TextField(blank=True)),
                ("scope", models.TextField(blank=True)),
                ("contribution_guidance", models.TextField(blank=True)),
                ("urgency", models.CharField(choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("critical", "Critical")], default="normal", max_length=20)),
                ("target_decision_date", models.DateField(blank=True, null=True)),
                ("contribution_deadline", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("framing", "Framing"), ("open_for_contribution", "Open for Contribution"), ("under_review", "Under Review"), ("ready_for_decision", "Ready for Decision"), ("decision_finalised", "Decision Finalised"), ("commitment", "Commitment"), ("implementation", "Implementation"), ("outcome_review", "Outcome Review"), ("lessons_learned", "Lessons Learned"), ("archived", "Archived")], default="draft", max_length=40)),
                ("status_changed_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decisions", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decisions", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_decisions", to=settings.AUTH_USER_MODEL)),
                ("workspace", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decisions", to="workspaces.workspace")),
            ],
            options={"ordering": ["-updated_at", "title", "id"]},
        ),
        migrations.CreateModel(
            name="DecisionTransition",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("sequence", models.PositiveIntegerField()),
                ("from_status", models.CharField(choices=[("draft", "Draft"), ("framing", "Framing"), ("open_for_contribution", "Open for Contribution"), ("under_review", "Under Review"), ("ready_for_decision", "Ready for Decision"), ("decision_finalised", "Decision Finalised"), ("commitment", "Commitment"), ("implementation", "Implementation"), ("outcome_review", "Outcome Review"), ("lessons_learned", "Lessons Learned"), ("archived", "Archived")], max_length=40)),
                ("to_status", models.CharField(choices=[("draft", "Draft"), ("framing", "Framing"), ("open_for_contribution", "Open for Contribution"), ("under_review", "Under Review"), ("ready_for_decision", "Ready for Decision"), ("decision_finalised", "Decision Finalised"), ("commitment", "Commitment"), ("implementation", "Implementation"), ("outcome_review", "Outcome Review"), ("lessons_learned", "Lessons Learned"), ("archived", "Archived")], max_length=40)),
                ("rationale", models.TextField(blank=True)),
                ("warnings_acknowledged", models.JSONField(blank=True, default=list)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_transitions", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transitions", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_transitions", to="organisations.organisation")),
            ],
            options={"ordering": ["sequence"]},
        ),
        migrations.AddConstraint(model_name="decision", constraint=models.CheckConstraint(condition=models.Q(("title", ""), _negated=True), name="decision_title_not_empty")),
        migrations.AddConstraint(model_name="decision", constraint=models.CheckConstraint(condition=models.Q(("status__in", ["draft", "framing", "open_for_contribution", "under_review", "ready_for_decision", "decision_finalised", "commitment", "implementation", "outcome_review", "lessons_learned", "archived"])), name="decision_status_valid")),
        migrations.AddConstraint(model_name="decision", constraint=models.CheckConstraint(condition=models.Q(("urgency__in", ["low", "normal", "high", "critical"])), name="decision_urgency_valid")),
        migrations.AddIndex(model_name="decision", index=models.Index(fields=["organisation", "status", "-updated_at"], name="decision_org_status_idx")),
        migrations.AddIndex(model_name="decision", index=models.Index(fields=["workspace", "status", "-updated_at"], name="decision_workspace_status_idx")),
        migrations.AddIndex(model_name="decision", index=models.Index(fields=["owner", "status", "-updated_at"], name="decision_owner_status_idx")),
        migrations.AddConstraint(model_name="decisiontransition", constraint=models.UniqueConstraint(fields=("decision", "sequence"), name="unique_transition_sequence_per_decision")),
        migrations.AddConstraint(model_name="decisiontransition", constraint=models.CheckConstraint(condition=models.Q(("from_status", models.F("to_status")), _negated=True), name="decision_transition_changes_status")),
        migrations.AddIndex(model_name="decisiontransition", index=models.Index(fields=["organisation", "-created_at"], name="transition_org_created_idx")),
    ]
