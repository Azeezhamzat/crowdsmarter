# Generated manually for the Phase 6 vertical slice.

import uuid

import django.db.models.deletion
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
            name="AIReview",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, editable=False),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("provider_key", models.CharField(max_length=120)),
                ("provider_label", models.CharField(max_length=240)),
                ("model_identifier", models.CharField(blank=True, max_length=240)),
                (
                    "prompt_version",
                    models.CharField(
                        default="decision-review-v1",
                        max_length=80,
                    ),
                ),
                ("input_fingerprint", models.CharField(max_length=64)),
                ("input_snapshot", models.JSONField(default=dict)),
                ("output", models.JSONField(blank=True, default=dict)),
                ("error_message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("review_notes", models.TextField(blank=True)),
                ("dismissed_at", models.DateTimeField(blank=True, null=True)),
                ("dismissal_reason", models.TextField(blank=True)),
                (
                    "decision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ai_reviews",
                        to="decisions.decision",
                    ),
                ),
                (
                    "dismissed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="dismissed_ai_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="ai_reviews",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "requested_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="requested_ai_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "reviewed_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="reviewed_ai_reviews",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="aireview",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    status__in=["pending", "running", "completed", "failed"]
                ),
                name="ai_review_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="aireview",
            constraint=models.CheckConstraint(
                condition=~models.Q(provider_key=""),
                name="ai_review_provider_not_empty",
            ),
        ),
        migrations.AddIndex(
            model_name="aireview",
            index=models.Index(
                fields=["decision", "-created_at"],
                name="ai_review_decision_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="aireview",
            index=models.Index(
                fields=["organisation", "status", "-created_at"],
                name="ai_review_org_status_idx",
            ),
        ),
    ]
