# Generated manually for the Phase 2 vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("decisions", "0001_initial"),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Participant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("decision_owner", "Decision Owner"), ("decision_maker", "Decision Maker"), ("contributor", "Contributor"), ("reviewer", "Reviewer"), ("observer", "Observer")], max_length=30)),
                ("status", models.CharField(choices=[("active", "Active"), ("removed", "Removed")], default="active", max_length=20)),
                ("removed_at", models.DateTimeField(blank=True, null=True)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="added_decision_participants", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="participants", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_participants", to="organisations.organisation")),
                ("removed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="removed_decision_participants", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_participations", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["role", "user__email", "id"]},
        ),
        migrations.AddConstraint(model_name="participant", constraint=models.UniqueConstraint(condition=models.Q(("status", "active")), fields=("decision", "user"), name="unique_active_participant_per_decision_user")),
        migrations.AddConstraint(model_name="participant", constraint=models.UniqueConstraint(condition=models.Q(("role", "decision_owner"), ("status", "active")), fields=("decision",), name="one_active_owner_participant_per_decision")),
        migrations.AddConstraint(model_name="participant", constraint=models.CheckConstraint(condition=models.Q(("role__in", ["decision_owner", "decision_maker", "contributor", "reviewer", "observer"])), name="participant_role_valid")),
        migrations.AddConstraint(model_name="participant", constraint=models.CheckConstraint(condition=models.Q(("status__in", ["active", "removed"])), name="participant_status_valid")),
        migrations.AddIndex(model_name="participant", index=models.Index(fields=["organisation", "status", "role"], name="participant_org_status_idx")),
        migrations.AddIndex(model_name="participant", index=models.Index(fields=["decision", "status", "role"], name="participant_decision_idx")),
    ]
