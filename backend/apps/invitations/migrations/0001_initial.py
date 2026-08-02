# Generated explicitly for the invitation vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.functions.text


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganisationInvitation",
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
                ("email", models.EmailField(max_length=254)),
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
                        choices=[
                            ("pending", "Pending"),
                            ("accepted", "Accepted"),
                            ("revoked", "Revoked"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("token_digest", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("last_sent_at", models.DateTimeField(blank=True, null=True)),
                ("send_count", models.PositiveSmallIntegerField(default=0)),
                (
                    "accepted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="accepted_organisation_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="sent_organisation_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="organisations.organisation",
                    ),
                ),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="organisationinvitation",
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower("email"),
                models.F("organisation"),
                name="unique_invite_email_ci_per_org",
            ),
        ),
        migrations.AddConstraint(
            model_name="organisationinvitation",
            constraint=models.CheckConstraint(
                condition=models.Q(role__in=["owner", "admin", "contributor", "viewer"]),
                name="invitation_role_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="organisationinvitation",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=["pending", "accepted", "revoked"]),
                name="invitation_status_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="organisationinvitation",
            constraint=models.CheckConstraint(
                condition=~models.Q(email=""),
                name="invitation_email_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="organisationinvitation",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        status="pending",
                        accepted_by__isnull=True,
                        accepted_at__isnull=True,
                        revoked_at__isnull=True,
                    )
                    | models.Q(
                        status="accepted",
                        accepted_by__isnull=False,
                        accepted_at__isnull=False,
                        revoked_at__isnull=True,
                    )
                    | models.Q(
                        status="revoked",
                        accepted_by__isnull=True,
                        accepted_at__isnull=True,
                        revoked_at__isnull=False,
                    )
                ),
                name="invitation_state_consistent",
            ),
        ),
        migrations.AddIndex(
            model_name="organisationinvitation",
            index=models.Index(
                fields=["organisation", "status", "-created_at"],
                name="invite_org_status_created_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="organisationinvitation",
            index=models.Index(
                fields=["email", "status"],
                name="invite_email_status_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="organisationinvitation",
            index=models.Index(fields=["expires_at"], name="invite_expires_idx"),
        ),
    ]
