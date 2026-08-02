# Generated explicitly for the Phase 1 foundation.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organisations", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
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
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("action", models.CharField(max_length=120)),
                ("object_type", models.CharField(max_length=120)),
                ("object_id", models.CharField(max_length=64)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="audit_events",
                        to="organisations.organisation",
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "indexes": [
                    models.Index(
                        fields=["organisation", "-created_at"],
                        name="audit_org_created_idx",
                    ),
                    models.Index(
                        fields=["object_type", "object_id"],
                        name="audit_object_idx",
                    ),
                    models.Index(
                        fields=["action", "-created_at"],
                        name="audit_action_created_idx",
                    ),
                ],
            },
        )
    ]
