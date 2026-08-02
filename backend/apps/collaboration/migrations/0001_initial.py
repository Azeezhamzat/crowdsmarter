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
            name="DiscussionEntry",
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
                    "kind",
                    models.CharField(
                        choices=[
                            ("note", "Note"),
                            ("question", "Question"),
                            ("concern", "Concern"),
                            ("update", "Update"),
                        ],
                        max_length=20,
                    ),
                ),
                ("body", models.TextField()),
                ("resolved_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_note", models.TextField(blank=True)),
                (
                    "author",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="discussion_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "decision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discussion_entries",
                        to="decisions.decision",
                    ),
                ),
                (
                    "mentioned_users",
                    models.ManyToManyField(
                        blank=True,
                        related_name="discussion_mentions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="discussion_entries",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "reply_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="replies",
                        to="collaboration.discussionentry",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="resolved_discussion_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.AddConstraint(
            model_name="discussionentry",
            constraint=models.CheckConstraint(
                condition=models.Q(kind__in=["note", "question", "concern", "update"]),
                name="discussion_entry_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="discussionentry",
            constraint=models.CheckConstraint(
                condition=~models.Q(body=""),
                name="discussion_entry_body_not_empty",
            ),
        ),
        migrations.AddConstraint(
            model_name="discussionentry",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(
                        resolved_at__isnull=True,
                        resolved_by__isnull=True,
                        resolution_note="",
                    )
                    | models.Q(
                        resolved_at__isnull=False,
                        resolved_by__isnull=False,
                    )
                ),
                name="discussion_resolution_fields_consistent",
            ),
        ),
        migrations.AddIndex(
            model_name="discussionentry",
            index=models.Index(
                fields=["decision", "-created_at"],
                name="discussion_decision_time_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="discussionentry",
            index=models.Index(
                fields=["organisation", "kind", "-created_at"],
                name="discussion_org_kind_idx",
            ),
        ),
    ]
