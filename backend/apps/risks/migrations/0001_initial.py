# Generated explicitly for the Phase 3 vertical slice.

import uuid

import django.core.validators
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
            name="Risk",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("description", models.TextField()),
                ("likelihood", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("impact", models.PositiveSmallIntegerField(validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)])),
                ("response_strategy", models.CharField(choices=[("accept", "Accept"), ("avoid", "Avoid"), ("mitigate", "Mitigate"), ("transfer", "Transfer"), ("monitor", "Monitor")], max_length=20)),
                ("mitigation_plan", models.TextField(blank=True)),
                ("review_date", models.DateField(blank=True, null=True)),
                ("status", models.CharField(choices=[("open", "Open"), ("monitoring", "Monitoring"), ("mitigated", "Mitigated"), ("accepted", "Accepted"), ("closed", "Closed")], default="open", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_decision_risks", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="risks", to="decisions.decision")),
                ("option", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="risks", to="decision_options.decisionoption")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="risks", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_decision_risks", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-likelihood", "-impact", "title", "id"]},
        ),
        migrations.AddConstraint(model_name="risk", constraint=models.CheckConstraint(condition=~models.Q(title=""), name="risk_title_not_empty")),
        migrations.AddConstraint(model_name="risk", constraint=models.CheckConstraint(condition=models.Q(likelihood__gte=1, likelihood__lte=5), name="risk_likelihood_between_1_and_5")),
        migrations.AddConstraint(model_name="risk", constraint=models.CheckConstraint(condition=models.Q(impact__gte=1, impact__lte=5), name="risk_impact_between_1_and_5")),
        migrations.AddConstraint(model_name="risk", constraint=models.CheckConstraint(condition=models.Q(response_strategy__in=["accept", "avoid", "mitigate", "transfer", "monitor"]), name="risk_response_strategy_valid")),
        migrations.AddConstraint(model_name="risk", constraint=models.CheckConstraint(condition=models.Q(status__in=["open", "monitoring", "mitigated", "accepted", "closed"]), name="risk_status_valid")),
        migrations.AddIndex(model_name="risk", index=models.Index(fields=["decision", "status"], name="risk_decision_status_idx")),
        migrations.AddIndex(model_name="risk", index=models.Index(fields=["organisation", "status"], name="risk_org_status_idx")),
    ]
