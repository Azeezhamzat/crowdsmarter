# Generated explicitly for the Phase 4 vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("decision_options", "0001_initial"),
        ("decisions", "0001_initial"),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionFinalisation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("rationale", models.TextField()),
                ("conditions", models.TextField(blank=True)),
                ("dissent_summary", models.TextField(blank=True)),
                ("position_snapshot", models.JSONField(default=list)),
                ("decided_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("decided_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finalised_decisions", to=settings.AUTH_USER_MODEL)),
                ("decision", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="finalisation", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_finalisations", to="organisations.organisation")),
                ("selected_option", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="finalisations", to="decision_options.decisionoption")),
            ],
            options={"ordering": ["-decided_at", "id"]},
        ),
        migrations.AddConstraint(model_name="decisionfinalisation", constraint=models.CheckConstraint(condition=~models.Q(rationale=""), name="finalisation_rationale_not_empty")),
        migrations.AddIndex(model_name="decisionfinalisation", index=models.Index(fields=["organisation", "-decided_at"], name="finalisation_org_date_idx")),
        migrations.AddIndex(model_name="decisionfinalisation", index=models.Index(fields=["selected_option", "-decided_at"], name="finalisation_option_idx")),
    ]
