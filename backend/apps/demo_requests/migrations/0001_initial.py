# Generated for CrowdSmarter Phase 15.1.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DemoRequest",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("full_name", models.CharField(max_length=160)),
                ("work_email", models.EmailField(max_length=254)),
                ("organisation_name", models.CharField(max_length=200)),
                ("job_title", models.CharField(blank=True, max_length=160)),
                ("organisation_size", models.CharField(choices=[("1-10", "1–10 people"), ("11-50", "11–50 people"), ("51-200", "51–200 people"), ("201-1000", "201–1,000 people"), ("1000+", "More than 1,000 people"), ("not_sure", "Not sure")], default="not_sure", max_length=20)),
                ("primary_need", models.CharField(choices=[("strategic_foresight", "Strategic foresight"), ("decision_governance", "Decision governance"), ("collective_intelligence", "Collective intelligence"), ("portfolio_prioritisation", "Portfolio prioritisation"), ("organisational_learning", "Organisational learning"), ("other", "Other")], max_length=40)),
                ("message", models.TextField(blank=True, max_length=2000)),
                ("consent_to_contact", models.BooleanField(default=False)),
                ("status", models.CharField(choices=[("new", "New"), ("contacted", "Contacted"), ("qualified", "Qualified"), ("closed", "Closed")], default="new", max_length=20)),
            ],
            options={"ordering": ["-created_at", "id"]},
        ),
        migrations.AddIndex(
            model_name="demorequest",
            index=models.Index(fields=["status", "created_at"], name="demo_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="demorequest",
            index=models.Index(fields=["work_email", "created_at"], name="demo_email_created_idx"),
        ),
        migrations.AddConstraint(
            model_name="demorequest",
            constraint=models.CheckConstraint(condition=~models.Q(full_name=""), name="demo_request_full_name_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="demorequest",
            constraint=models.CheckConstraint(condition=~models.Q(organisation_name=""), name="demo_request_organisation_not_empty"),
        ),
        migrations.AddConstraint(
            model_name="demorequest",
            constraint=models.CheckConstraint(condition=models.Q(consent_to_contact=True), name="demo_request_contact_consent_required"),
        ),
    ]
