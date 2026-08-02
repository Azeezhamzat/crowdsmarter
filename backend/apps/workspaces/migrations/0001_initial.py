# Generated manually for the Phase 2 vertical slice.

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Workspace",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=160)),
                ("slug", models.SlugField(max_length=80)),
                ("description", models.TextField(blank=True)),
                ("is_default", models.BooleanField(default=False)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_workspaces", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="workspaces", to="organisations.organisation")),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.AddConstraint(
            model_name="workspace",
            constraint=models.UniqueConstraint(fields=("organisation", "slug"), name="unique_workspace_slug_per_org"),
        ),
        migrations.AddConstraint(
            model_name="workspace",
            constraint=models.UniqueConstraint(condition=models.Q(("is_default", True)), fields=("organisation",), name="one_default_workspace_per_org"),
        ),
        migrations.AddConstraint(
            model_name="workspace",
            constraint=models.CheckConstraint(condition=models.Q(("name", ""), _negated=True), name="workspace_name_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="workspace",
            constraint=models.CheckConstraint(condition=models.Q(("slug", ""), _negated=True), name="workspace_slug_not_empty"),
        ),
        migrations.AddIndex(
            model_name="workspace",
            index=models.Index(fields=["organisation", "name"], name="workspace_org_name_idx"),
        ),
    ]
