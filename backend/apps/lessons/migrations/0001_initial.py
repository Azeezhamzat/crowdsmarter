# Generated manually for the Phase 5 vertical slice.

import django.db.models.deletion
import uuid
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
            name="Lesson",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=240)),
                ("insight", models.TextField()),
                ("category", models.CharField(choices=[("process", "Decision process"), ("evidence", "Evidence quality"), ("assumption", "Assumption"), ("stakeholder", "Stakeholder involvement"), ("implementation", "Implementation"), ("outcome", "Outcome"), ("other", "Other")], max_length=30)),
                ("applicability", models.TextField()),
                ("recommended_change", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("active", "Active"), ("retired", "Retired")], default="active", max_length=20)),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="created_lessons", to=settings.AUTH_USER_MODEL)),
                ("decision", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="decisions.decision")),
                ("organisation", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="lessons", to="organisations.organisation")),
                ("retired_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="retired_lessons", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-created_at", "title", "id"]},
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.CheckConstraint(condition=~models.Q(title=""), name="lesson_title_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.CheckConstraint(condition=~models.Q(insight=""), name="lesson_insight_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.CheckConstraint(condition=~models.Q(applicability=""), name="lesson_applicability_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.CheckConstraint(condition=models.Q(category__in=["process", "evidence", "assumption", "stakeholder", "implementation", "outcome", "other"]), name="lesson_category_valid"),
        ),
        migrations.AddConstraint(
            model_name="lesson",
            constraint=models.CheckConstraint(condition=models.Q(status__in=["active", "retired"]), name="lesson_status_valid"),
        ),
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(fields=["organisation", "status", "-created_at"], name="lesson_org_status_idx"),
        ),
        migrations.AddIndex(
            model_name="lesson",
            index=models.Index(fields=["decision", "status", "-created_at"], name="lesson_decision_status_idx"),
        ),
    ]
