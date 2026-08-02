# Generated for CrowdSmarter Phase 17.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("methodology", "0001_initial"),
        ("decisions", "0004_decision_organisation_method"),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionMethodUsage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("applied_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="applied_decision_methods", to=settings.AUTH_USER_MODEL)),
                ("decision", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="method_usage", to="decisions.decision")),
                ("method_version", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="usages", to="methodology.decisionmethodversion")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_method_usages", to="organisations.organisation")),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddIndex(model_name="decisionmethodusage", index=models.Index(fields=["organisation", "-created_at"], name="method_usage_org_idx")),
    ]
