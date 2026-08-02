# Generated manually for Phase 11.

import django.db.models.deletion
import apps.foresight.models
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organisations", "0001_initial"),
        ("decisions", "0003_decision_template_provenance"),
    ]

    operations = [
        migrations.CreateModel(
            name="Source",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=300)),
                ("source_type", models.CharField(choices=[("research", "Research publication"), ("news", "News or media"), ("government", "Government or regulation"), ("internal", "Internal organisational record"), ("expert", "Expert contribution"), ("stakeholder", "Stakeholder contribution"), ("dataset", "Dataset"), ("other", "Other")], max_length=30)),
                ("author", models.CharField(blank=True, max_length=240)),
                ("publisher", models.CharField(blank=True, max_length=240)),
                ("published_on", models.DateField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True, max_length=1200)),
                ("reference", models.CharField(blank=True, max_length=800)),
                ("credibility", models.CharField(choices=[("unassessed", "Not assessed"), ("low", "Low"), ("moderate", "Moderate"), ("high", "High")], default="unassessed", max_length=20)),
                ("credibility_rationale", models.TextField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("superseded", "Superseded"), ("withdrawn", "Withdrawn")], default="active", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_foresight_sources", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="foresight_sources", to="organisations.organisation")),
                ("supersedes", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="superseded_by", to="foresight.source")),
            ],
            options={"ordering": ["-published_on", "-created_at", "title"]},
        ),
        migrations.CreateModel(
            name="Signal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=280)),
                ("summary", models.TextField()),
                ("future_implication", models.TextField()),
                ("steep_category", models.CharField(choices=[("social", "Social"), ("technological", "Technological"), ("economic", "Economic"), ("environmental", "Environmental"), ("political", "Political"), ("legal", "Legal"), ("ethical", "Ethical")], max_length=30)),
                ("time_horizon", models.CharField(choices=[("near", "Near term (0–2 years)"), ("medium", "Medium term (3–5 years)"), ("long", "Long term (6+ years)")], max_length=20)),
                ("maturity", models.CharField(choices=[("weak", "Weak signal"), ("emerging", "Emerging pattern"), ("established", "Established trend")], max_length=20)),
                ("polarity", models.CharField(choices=[("opportunity", "Opportunity"), ("threat", "Threat"), ("both", "Opportunity and threat"), ("unclear", "Unclear")], default="unclear", max_length=20)),
                ("geography", models.CharField(blank=True, max_length=160)),
                ("domain", models.CharField(blank=True, max_length=160)),
                ("impact", models.PositiveSmallIntegerField(default=3)),
                ("uncertainty", models.PositiveSmallIntegerField(default=3)),
                ("status", models.CharField(choices=[("draft", "Draft"), ("reviewed", "Reviewed"), ("monitoring", "Monitoring"), ("retired", "Retired")], default="draft", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_foresight_signals", to=settings.AUTH_USER_MODEL)),
                ("last_reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="reviewed_foresight_signals", to=settings.AUTH_USER_MODEL)),
                ("last_reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="foresight_signals", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_foresight_signals", to=settings.AUTH_USER_MODEL)),
                ("source", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="signals", to="foresight.source")),
            ],
            options={"ordering": ["-impact", "-created_at", "title"]},
        ),
        migrations.CreateModel(
            name="SourceAttachment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("file", models.FileField(max_length=600, upload_to=apps.foresight.models.source_attachment_path)),
                ("original_name", models.CharField(max_length=255)),
                ("content_type", models.CharField(max_length=160)),
                ("size_bytes", models.PositiveBigIntegerField()),
                ("sha256", models.CharField(max_length=64)),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="foresight.source")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_source_attachments", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["created_at", "original_name"]},
        ),
        migrations.CreateModel(
            name="Watchlist",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=180)),
                ("description", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_foresight_watchlists", to=settings.AUTH_USER_MODEL)),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="foresight_watchlists", to="organisations.organisation")),
                ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="owned_foresight_watchlists", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["name", "id"]},
        ),
        migrations.CreateModel(
            name="SignalDecisionLink",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("relevance", models.TextField()),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signal_links", to="decisions.decision")),
                ("linked_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="linked_signal_decisions", to=settings.AUTH_USER_MODEL)),
                ("signal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="decision_links", to="foresight.signal")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="WatchlistSignal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("note", models.CharField(blank=True, max_length=500)),
                ("added_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="added_watchlist_signals", to=settings.AUTH_USER_MODEL)),
                ("signal", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="watchlist_links", to="foresight.signal")),
                ("watchlist", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="signal_links", to="foresight.watchlist")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddField(
            model_name="watchlist",
            name="signals",
            field=models.ManyToManyField(related_name="watchlists", through="foresight.WatchlistSignal", to="foresight.signal"),
        ),
        migrations.AddConstraint(model_name="source", constraint=models.CheckConstraint(condition=~models.Q(title=""), name="foresight_source_title_not_empty")),
        migrations.AddConstraint(model_name="source", constraint=models.CheckConstraint(condition=models.Q(source_type__in=["research", "news", "government", "internal", "expert", "stakeholder", "dataset", "other"]), name="foresight_source_type_valid")),
        migrations.AddConstraint(model_name="source", constraint=models.CheckConstraint(condition=models.Q(credibility__in=["unassessed", "low", "moderate", "high"]), name="foresight_source_credibility_valid")),
        migrations.AddConstraint(model_name="source", constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "superseded", "withdrawn"]), name="foresight_source_status_valid")),
        migrations.AddIndex(model_name="source", index=models.Index(fields=["organisation", "status", "source_type"], name="foresight_source_org_idx")),
        migrations.AddIndex(model_name="source", index=models.Index(fields=["organisation", "credibility"], name="foresight_source_cred_idx")),
        migrations.AddConstraint(model_name="sourceattachment", constraint=models.UniqueConstraint(fields=("source", "sha256"), name="unique_source_attachment_hash")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=~models.Q(title=""), name="foresight_signal_title_not_empty")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(impact__gte=1, impact__lte=5), name="signal_impact_1_to_5")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(uncertainty__gte=1, uncertainty__lte=5), name="signal_uncertainty_1_to_5")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(steep_category__in=["social", "technological", "economic", "environmental", "political", "legal", "ethical"]), name="signal_steep_valid")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(time_horizon__in=["near", "medium", "long"]), name="signal_horizon_valid")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(maturity__in=["weak", "emerging", "established"]), name="signal_maturity_valid")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(polarity__in=["opportunity", "threat", "both", "unclear"]), name="signal_polarity_valid")),
        migrations.AddConstraint(model_name="signal", constraint=models.CheckConstraint(condition=models.Q(status__in=["draft", "reviewed", "monitoring", "retired"]), name="signal_status_valid")),
        migrations.AddIndex(model_name="signal", index=models.Index(fields=["organisation", "status", "steep_category"], name="signal_org_steep_idx")),
        migrations.AddIndex(model_name="signal", index=models.Index(fields=["organisation", "time_horizon", "maturity"], name="signal_org_horizon_idx")),
        migrations.AddConstraint(model_name="watchlist", constraint=models.UniqueConstraint(fields=("organisation", "name"), name="unique_watchlist_name_per_org")),
        migrations.AddConstraint(model_name="watchlist", constraint=models.CheckConstraint(condition=~models.Q(name=""), name="watchlist_name_not_empty")),
        migrations.AddConstraint(model_name="watchlistsignal", constraint=models.UniqueConstraint(fields=("watchlist", "signal"), name="unique_signal_per_watchlist")),
        migrations.AddConstraint(model_name="signaldecisionlink", constraint=models.UniqueConstraint(fields=("signal", "decision"), name="unique_signal_decision_link")),
    ]
