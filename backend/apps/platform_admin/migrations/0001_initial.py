# Generated for CrowdSmarter Phase 18B.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0002_administration_and_membership_history"),
    ]

    operations = [
        migrations.CreateModel(
            name="PlatformConfiguration",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("singleton_key", models.PositiveSmallIntegerField(default=1, editable=False, unique=True)),
                ("public_contact_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("demo_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("support_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("privacy_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("security_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("notification_sender_email", models.EmailField(default="hello@crowdsmarter.com", max_length=254)),
                ("support_access_max_hours", models.PositiveSmallIntegerField(default=8)),
            ],
            options={
                "verbose_name": "platform configuration",
                "verbose_name_plural": "platform configuration",
            },
        ),
        migrations.CreateModel(
            name="PlatformAdministrator",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("suspended", "Suspended")], default="active", max_length=20)),
                ("rationale", models.TextField()),
                ("suspended_at", models.DateTimeField(blank=True, null=True)),
                ("granted_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="granted_platform_administrator_roles", to=settings.AUTH_USER_MODEL)),
                ("suspended_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="suspended_platform_administrator_roles", to=settings.AUTH_USER_MODEL)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="platform_administrator", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["user__email"]},
        ),
        migrations.CreateModel(
            name="SupportAccessGrant",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("access_level", models.CharField(choices=[("read_only", "Read-only support"), ("operational", "Operational support")], default="read_only", max_length=20)),
                ("reason", models.TextField()),
                ("status", models.CharField(choices=[("active", "Active"), ("revoked", "Revoked"), ("expired", "Expired")], default="active", max_length=20)),
                ("expires_at", models.DateTimeField()),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("administrator", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="platform_support_access_grants", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="platform_support_access_grants", to="organisations.organisation")),
                ("revoked_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="revoked_platform_support_access_grants", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="platformconfiguration",
            constraint=models.CheckConstraint(condition=models.Q(("singleton_key", 1)), name="platform_configuration_singleton_key_one"),
        ),
        migrations.AddConstraint(
            model_name="platformconfiguration",
            constraint=models.CheckConstraint(condition=models.Q(("support_access_max_hours__gte", 1), ("support_access_max_hours__lte", 72)), name="platform_support_access_hours_range"),
        ),
        migrations.AddConstraint(
            model_name="platformadministrator",
            constraint=models.CheckConstraint(condition=models.Q(("status__in", ["active", "suspended"])), name="platform_administrator_status_valid"),
        ),
        migrations.AddConstraint(
            model_name="platformadministrator",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("status", "active"), ("suspended_at__isnull", True), ("suspended_by__isnull", True)), models.Q(("status", "suspended"), ("suspended_at__isnull", False), ("suspended_by__isnull", False)), _connector="OR"), name="platform_administrator_suspension_consistent"),
        ),
        migrations.AddConstraint(
            model_name="platformadministrator",
            constraint=models.CheckConstraint(condition=models.Q(("rationale", ""), _negated=True), name="platform_administrator_rationale_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="supportaccessgrant",
            constraint=models.CheckConstraint(condition=models.Q(("access_level__in", ["read_only", "operational"])), name="support_access_level_valid"),
        ),
        migrations.AddConstraint(
            model_name="supportaccessgrant",
            constraint=models.CheckConstraint(condition=models.Q(("status__in", ["active", "revoked", "expired"])), name="support_access_status_valid"),
        ),
        migrations.AddConstraint(
            model_name="supportaccessgrant",
            constraint=models.CheckConstraint(condition=models.Q(("reason", ""), _negated=True), name="support_access_reason_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="supportaccessgrant",
            constraint=models.CheckConstraint(condition=models.Q(models.Q(("status", "active"), ("revoked_at__isnull", True), ("revoked_by__isnull", True)), models.Q(("status", "expired"), ("revoked_at__isnull", True), ("revoked_by__isnull", True)), models.Q(("status", "revoked"), ("revoked_at__isnull", False), ("revoked_by__isnull", False)), _connector="OR"), name="support_access_revocation_consistent"),
        ),
        migrations.AddIndex(
            model_name="supportaccessgrant",
            index=models.Index(fields=["administrator", "status", "expires_at"], name="support_admin_status_exp_idx"),
        ),
        migrations.AddIndex(
            model_name="supportaccessgrant",
            index=models.Index(fields=["organisation", "status", "expires_at"], name="support_org_status_exp_idx"),
        ),
    ]
