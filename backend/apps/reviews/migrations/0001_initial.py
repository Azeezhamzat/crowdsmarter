# Generated manually for the Phase 5 vertical slice.

import django.db.models.deletion
import django.utils.timezone
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("decisions", "0002_decisionfinalisation"),
        ("organisations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DecisionReview",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("commitment_statement", models.TextField()),
                ("success_measures", models.TextField()),
                ("review_due_date", models.DateField()),
                ("commitment_rationale", models.TextField()),
                ("commitment_recorded_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("implementation_plan", models.TextField(blank=True)),
                ("implementation_started_at", models.DateTimeField(blank=True, null=True)),
                ("implementation_summary", models.TextField(blank=True)),
                ("outcome_summary", models.TextField(blank=True)),
                ("outcome_assessment", models.CharField(blank=True, choices=[("exceeded", "Exceeded expectations"), ("met", "Met expectations"), ("partially_met", "Partially met expectations"), ("not_met", "Did not meet expectations"), ("inconclusive", "Inconclusive")], max_length=30)),
                ("review_evidence", models.TextField(blank=True)),
                ("unintended_consequences", models.TextField(blank=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("commitment_recorded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="recorded_decision_commitments", to=settings.AUTH_USER_MODEL)),
                ("decision", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="review", to="decisions.decision")),
                ("implementation_owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_decision_reviews", to=settings.AUTH_USER_MODEL)),
                ("implementation_started_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="started_decision_implementations", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="decision_reviews", to="organisations.organisation")),
                ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="completed_decision_reviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="decisionreview",
            constraint=models.CheckConstraint(condition=~models.Q(commitment_statement=""), name="review_commitment_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="decisionreview",
            constraint=models.CheckConstraint(condition=~models.Q(success_measures=""), name="review_measures_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="decisionreview",
            constraint=models.CheckConstraint(condition=models.Q(outcome_assessment="") | models.Q(outcome_assessment__in=["exceeded", "met", "partially_met", "not_met", "inconclusive"]), name="review_outcome_assessment_valid"),
        ),
        migrations.AddIndex(
            model_name="decisionreview",
            index=models.Index(fields=["organisation", "review_due_date"], name="review_org_due_idx"),
        ),
        migrations.AddIndex(
            model_name="decisionreview",
            index=models.Index(fields=["implementation_owner", "review_due_date"], name="review_owner_due_idx"),
        ),
    ]
