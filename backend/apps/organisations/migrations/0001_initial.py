# Generated explicitly for the Phase 1 foundation.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Organisation",
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
                ("name", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=80, unique=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_organisations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name", "id"],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("name", ""), _negated=True),
                        name="organisation_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("slug", ""), _negated=True),
                        name="organisation_slug_not_empty",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Membership",
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
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("owner", "Owner"),
                            ("admin", "Administrator"),
                            ("contributor", "Contributor"),
                            ("viewer", "Viewer"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("active", "Active"), ("suspended", "Suspended")],
                        default="active",
                        max_length=20,
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="organisation_memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["user__email"],
                "indexes": [
                    models.Index(
                        fields=["organisation", "role", "status"],
                        name="org_members_role_status_idx",
                    ),
                    models.Index(fields=["user", "status"], name="org_members_user_status_idx"),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("organisation", "user"),
                        name="unique_active_or_inactive_membership_per_user_org",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("role__in", ["owner", "admin", "contributor", "viewer"])
                        ),
                        name="membership_role_valid",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("status__in", ["active", "suspended"])),
                        name="membership_status_valid",
                    ),
                ],
            },
        ),
    ]
