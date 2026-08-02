# Generated for CrowdSmarter Phase 17.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


def seed_membership_history(apps, schema_editor):  # type: ignore[no-untyped-def]
    Membership = apps.get_model("organisations", "Membership")
    MembershipEvent = apps.get_model("organisations", "MembershipEvent")
    for membership in Membership.objects.all().iterator():
        MembershipEvent.objects.create(
            organisation_id=membership.organisation_id,
            membership_id_snapshot=membership.id,
            user_id=membership.user_id,
            actor_id=membership.organisation.created_by_id,
            kind="created",
            new_role=membership.role,
            new_status=membership.status,
            note="Imported baseline membership when Phase 17 history was introduced.",
        )


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(model_name="organisation", name="description", field=models.TextField(blank=True)),
        migrations.AddField(model_name="organisation", name="website_url", field=models.URLField(blank=True)),
        migrations.AddField(model_name="organisation", name="brand_name", field=models.CharField(blank=True, max_length=120)),
        migrations.AddField(
            model_name="organisation", name="primary_colour",
            field=models.CharField(default="#315c54", max_length=7, validators=[django.core.validators.RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use a six-digit hexadecimal colour.")]),
        ),
        migrations.AddField(
            model_name="organisation", name="invitation_policy",
            field=models.CharField(choices=[("owners_and_admins", "Owners and administrators"), ("owners_only", "Owners only")], default="owners_and_admins", max_length=30),
        ),
        migrations.AddField(
            model_name="organisation", name="default_invitation_role",
            field=models.CharField(choices=[("admin", "Administrator"), ("contributor", "Contributor"), ("viewer", "Viewer")], default="contributor", max_length=20),
        ),
        migrations.AddField(model_name="organisation", name="retention_days", field=models.PositiveIntegerField(blank=True, null=True)),
        migrations.AddField(
            model_name="organisation", name="status",
            field=models.CharField(choices=[("active", "Active"), ("deactivated", "Deactivated")], default="active", max_length=20),
        ),
        migrations.AddField(model_name="organisation", name="deactivated_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(
            model_name="organisation", name="deactivated_by",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="deactivated_organisations", to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name="MembershipEvent",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("membership_id_snapshot", models.UUIDField(blank=True, null=True)),
                ("kind", models.CharField(choices=[("created", "Created"), ("role_changed", "Role changed"), ("removed", "Removed"), ("ownership_transferred", "Ownership transferred"), ("status_changed", "Status changed")], max_length=30)),
                ("previous_role", models.CharField(blank=True, max_length=20)),
                ("new_role", models.CharField(blank=True, max_length=20)),
                ("previous_status", models.CharField(blank=True, max_length=20)),
                ("new_status", models.CharField(blank=True, max_length=20)),
                ("note", models.TextField(blank=True)),
                ("actor", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="performed_membership_events", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="membership_events", to="organisations.organisation")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="organisation_membership_events", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.RunPython(seed_membership_history, migrations.RunPython.noop),
        migrations.CreateModel(
            name="OrganisationDeletionRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("cancelled", "Cancelled"), ("completed", "Completed")], default="pending", max_length=20)),
                ("reason", models.TextField()),
                ("earliest_deletion_at", models.DateTimeField()),
                ("cancelled_at", models.DateTimeField(blank=True, null=True)),
                ("cancelled_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="cancelled_organisation_deletions", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="deletion_requests", to="organisations.organisation")),
                ("requested_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="requested_organisation_deletions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddConstraint(model_name="organisation", constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "deactivated"]), name="organisation_status_valid")),
        migrations.AddConstraint(model_name="organisation", constraint=models.CheckConstraint(condition=models.Q(invitation_policy__in=["owners_and_admins", "owners_only"]), name="organisation_invitation_policy_valid")),
        migrations.AddConstraint(model_name="organisation", constraint=models.CheckConstraint(condition=models.Q(default_invitation_role__in=["admin", "contributor", "viewer"]), name="organisation_default_invite_role_valid")),
        migrations.AddConstraint(
            model_name="organisation",
            constraint=models.CheckConstraint(
                condition=(models.Q(status="active", deactivated_at__isnull=True, deactivated_by__isnull=True) | models.Q(status="deactivated", deactivated_at__isnull=False, deactivated_by__isnull=False)),
                name="organisation_deactivation_state_consistent",
            ),
        ),
        migrations.AddConstraint(model_name="membershipevent", constraint=models.CheckConstraint(condition=models.Q(kind__in=["created", "role_changed", "removed", "ownership_transferred", "status_changed"]), name="membership_event_kind_valid")),
        migrations.AddIndex(model_name="membershipevent", index=models.Index(fields=["organisation", "-created_at"], name="member_event_org_idx")),
        migrations.AddConstraint(model_name="organisationdeletionrequest", constraint=models.CheckConstraint(condition=models.Q(status__in=["pending", "cancelled", "completed"]), name="organisation_deletion_status_valid")),
        migrations.AddConstraint(model_name="organisationdeletionrequest", constraint=models.UniqueConstraint(condition=models.Q(status="pending"), fields=("organisation",), name="one_pending_deletion_request_per_org")),
    ]
