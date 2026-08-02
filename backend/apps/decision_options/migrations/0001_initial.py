# Generated explicitly for the Phase 3 vertical slice.

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
            name="DecisionOption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("description", models.TextField()),
                ("expected_benefits", models.TextField(blank=True)),
                ("tradeoffs", models.TextField(blank=True)),
                ("is_status_quo", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("active", "Active"), ("withdrawn", "Withdrawn")], default="active", max_length=20)),
                ("withdrawn_at", models.DateTimeField(blank=True, null=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decision_options", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="options", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_options", to="organisations.organisation")),
                ("proposed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="proposed_decision_options", to=settings.AUTH_USER_MODEL)),
                ("withdrawn_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="withdrawn_decision_options", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-is_status_quo", "created_at", "title", "id"]},
        ),
        migrations.AddConstraint(model_name="decisionoption", constraint=models.CheckConstraint(condition=~models.Q(title=""), name="decision_option_title_not_empty")),
        migrations.AddConstraint(model_name="decisionoption", constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "withdrawn"]), name="decision_option_status_valid")),
        migrations.AddConstraint(model_name="decisionoption", constraint=models.UniqueConstraint(condition=models.Q(is_status_quo=True, status="active"), fields=("decision",), name="one_active_status_quo_option_per_decision")),
        migrations.AddIndex(model_name="decisionoption", index=models.Index(fields=["decision", "status", "created_at"], name="option_decision_status_idx")),
        migrations.AddIndex(model_name="decisionoption", index=models.Index(fields=["organisation", "status"], name="option_org_status_idx")),
    ]
