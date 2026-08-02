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
            name="Notification",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("assignment", "Assignment"),
                            ("lifecycle", "Lifecycle"),
                            ("review_due", "Review Due"),
                            ("ai_review", "AI Review"),
                            ("membership", "Membership"),
                            ("system", "System"),
                        ],
                        max_length=30,
                    ),
                ),
                ("title", models.CharField(max_length=240)),
                ("message", models.TextField()),
                ("url", models.CharField(blank=True, max_length=500)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("dedup_key", models.CharField(blank=True, max_length=180)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                (
                    "decision",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="decisions.decision",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=~models.Q(title=""),
                name="notification_title_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    kind__in=[
                        "assignment",
                        "lifecycle",
                        "review_due",
                        "ai_review",
                        "membership",
                        "system",
                    ]
                ),
                name="notification_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="notification",
            constraint=models.UniqueConstraint(
                condition=~models.Q(dedup_key=""),
                fields=("recipient", "dedup_key"),
                name="notification_recipient_dedup_unique",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="notification_inbox_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="notification",
            index=models.Index(
                fields=["organisation", "-created_at"],
                name="notification_org_idx",
            ),
        ),
    ]
