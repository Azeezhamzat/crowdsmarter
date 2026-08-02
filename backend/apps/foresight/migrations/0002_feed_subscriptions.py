# Generated manually for Phase 11 RSS/Atom ingestion.

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("foresight", "0001_initial"),
        ("organisations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="FeedSubscription",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=200)),
                ("feed_url", models.URLField(max_length=1200)),
                ("is_active", models.BooleanField(default=True)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_success_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.CharField(blank=True, max_length=1000)),
                ("etag", models.CharField(blank=True, max_length=500)),
                ("last_modified", models.CharField(blank=True, max_length=500)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_foresight_feeds", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="foresight_feeds", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_foresight_feeds", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.AddField(
            model_name="source",
            name="external_id",
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name="source",
            name="feed",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="imported_sources", to="foresight.feedsubscription"),
        ),
        migrations.AddConstraint(
            model_name="feedsubscription",
            constraint=models.UniqueConstraint(fields=("organisation", "feed_url"), name="unique_feed_url_per_org"),
        ),
        migrations.AddConstraint(
            model_name="feedsubscription",
            constraint=models.CheckConstraint(condition=~models.Q(name=""), name="foresight_feed_name_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="source",
            constraint=models.UniqueConstraint(condition=~models.Q(external_id=""), fields=("feed", "external_id"), name="unique_feed_external_source"),
        ),
    ]
