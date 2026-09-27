import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("contributions", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="facilitationsession",
            name="fixed_constraints",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="facilitationsession",
            name="influence_boundary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="facilitationsession",
            name="missing_perspectives",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="facilitationsession",
            name="participation_channels",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="FacilitationRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("agreement", "Agreement"),
                            ("disagreement", "Unresolved disagreement"),
                            ("action", "Action"),
                            ("evidence_gap", "Evidence gap"),
                            ("next_question", "Next question"),
                            ("participant_statement", "Participant statement"),
                        ],
                        max_length=30,
                    ),
                ),
                ("body", models.TextField()),
                (
                    "channel",
                    models.CharField(
                        choices=[
                            ("in_person", "In person"),
                            ("phone", "Telephone"),
                            ("paper", "Paper"),
                            ("partner_assisted", "Partner assisted"),
                            ("digital", "Digital"),
                            ("other", "Other"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "origin",
                    models.CharField(
                        choices=[
                            ("participant_input", "Participant input"),
                            ("facilitator_synthesis", "Facilitator synthesis"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "attribution",
                    models.CharField(
                        choices=[
                            ("attributed", "Attributed"),
                            ("anonymous", "Anonymous"),
                            ("confidential", "Confidential"),
                        ],
                        default="anonymous",
                        max_length=20,
                    ),
                ),
                ("speaker_label", models.CharField(blank=True, max_length=240)),
                ("permission_to_quote", models.BooleanField(default=False)),
                ("follow_up_owner", models.CharField(blank=True, max_length=240)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_facilitation_records",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "decision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="facilitation_records",
                        to="decisions.decision",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="facilitation_records",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "session",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="records",
                        to="contributions.facilitationsession",
                    ),
                ),
                (
                    "source_participant",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="facilitation_records",
                        to="contributions.sessionparticipant",
                    ),
                ),
            ],
            options={"ordering": ["created_at", "id"]},
        ),
        migrations.CreateModel(
            name="FacilitationAuthorityResponse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("what_we_heard", models.TextField(blank=True)),
                ("what_changed", models.TextField(blank=True)),
                ("what_did_not_change", models.TextField(blank=True)),
                ("rationale", models.TextField(blank=True)),
                ("next_steps", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[("draft", "Draft"), ("published", "Published")],
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                (
                    "decision",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="facilitation_authority_responses",
                        to="decisions.decision",
                    ),
                ),
                (
                    "organisation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="facilitation_authority_responses",
                        to="organisations.organisation",
                    ),
                ),
                (
                    "published_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_facilitation_responses",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "session",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="authority_response",
                        to="contributions.facilitationsession",
                    ),
                ),
            ],
            options={"ordering": ["session", "id"]},
        ),
        migrations.AddIndex(
            model_name="facilitationrecord",
            index=models.Index(
                fields=["session", "kind", "created_at"], name="fac_record_session_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="facilitationrecord",
            index=models.Index(
                fields=["decision", "channel"], name="fac_record_decision_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    kind__in=[
                        "agreement",
                        "disagreement",
                        "action",
                        "evidence_gap",
                        "next_question",
                        "participant_statement",
                    ]
                ),
                name="facilitation_record_kind_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    channel__in=[
                        "in_person",
                        "phone",
                        "paper",
                        "partner_assisted",
                        "digital",
                        "other",
                    ]
                ),
                name="facilitation_record_channel_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(attribution__in=["attributed", "anonymous", "confidential"]),
                name="facilitation_attribution_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationrecord",
            constraint=models.CheckConstraint(
                condition=models.Q(origin__in=["participant_input", "facilitator_synthesis"]),
                name="facilitation_record_origin_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationrecord",
            constraint=models.CheckConstraint(
                condition=~models.Q(body=""), name="facilitation_record_body_not_empty"
            ),
        ),
        migrations.AddConstraint(
            model_name="facilitationauthorityresponse",
            constraint=models.CheckConstraint(
                condition=models.Q(status__in=["draft", "published"]),
                name="facilitation_response_status_valid",
            ),
        ),
    ]
