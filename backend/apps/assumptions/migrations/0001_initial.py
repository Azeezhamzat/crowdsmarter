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
            name="Assumption",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("statement", models.TextField()),
                ("rationale", models.TextField(blank=True)),
                ("impact_if_false", models.TextField()),
                ("confidence", models.CharField(choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")], max_length=20)),
                ("verification_status", models.CharField(choices=[("unverified", "Unverified"), ("partially_verified", "Partially Verified"), ("verified", "Verified"), ("invalidated", "Invalidated")], default="unverified", max_length=30)),
                ("verification_notes", models.TextField(blank=True)),
                ("review_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("retired", "Retired")], default="active", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_assumptions", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assumptions", to="decisions.decision")),
                ("option", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="assumptions", to="decision_options.decisionoption")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assumptions", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_assumptions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["verification_status", "-confidence", "created_at", "id"]},
        ),
        migrations.AddConstraint(model_name="assumption", constraint=models.CheckConstraint(condition=~models.Q(statement=""), name="assumption_statement_not_empty")),
        migrations.AddConstraint(model_name="assumption", constraint=models.CheckConstraint(condition=models.Q(confidence__in=["low", "medium", "high"]), name="assumption_confidence_valid")),
        migrations.AddConstraint(model_name="assumption", constraint=models.CheckConstraint(condition=models.Q(verification_status__in=["unverified", "partially_verified", "verified", "invalidated"]), name="assumption_verification_status_valid")),
        migrations.AddConstraint(model_name="assumption", constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "retired"]), name="assumption_status_valid")),
        migrations.AddIndex(model_name="assumption", index=models.Index(fields=["decision", "status", "verification_status"], name="assumption_decision_idx")),
        migrations.AddIndex(model_name="assumption", index=models.Index(fields=["organisation", "status"], name="assumption_org_status_idx")),
    ]
